import os
from collections.abc import AsyncGenerator
from urllib.parse import urlparse, urlunparse

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from main import app
from src.core.settings import settings
from src.db.database import get_session
from src.lib.limiter import limiter
from src.modules.comment_moderation.models import CommentModeration
from src.modules.comments.models import Comment
from src.modules.developers.models import Developer
from src.modules.games.models import Game
from src.modules.genres.models import Genre
from src.modules.likes.models import Like
from src.modules.password_reset_tokens.models import PasswordResetToken
from src.modules.platforms.models import Platform
from src.modules.publisher.models import Publisher
from src.modules.reports.models import Report
from src.modules.review_moderation.models import ReviewModeration
from src.modules.reviews.models import Review
from src.modules.stores.models import Store
from src.modules.users.models import User
from src.modules.wishlists.models import Wishlist
from src.services.gemini.dependencies import get_gemini_service
from src.services.mailer.dependencies import get_mailer_service
from src.services.moderation_producer.dependencies import get_producer_service
from src.services.moderation_producer.schemas import ModerationPayload
from src.services.storage.dependencies import get_storage_service

REGISTERED_MODELS = (
    Comment,
    CommentModeration,
    Developer,
    Game,
    Genre,
    Like,
    PasswordResetToken,
    Platform,
    Publisher,
    Report,
    Review,
    ReviewModeration,
    Store,
    User,
    Wishlist,
)


def get_test_database_url() -> str:
    explicit_url = os.environ.get("TEST_DATABASE_URL")
    if explicit_url:
        return explicit_url
    parsed = urlparse(settings.DATABASE_URL)
    return urlunparse(parsed._replace(path="/pixel_reviews_test"))


async def ensure_test_database_exists(test_db_url: str) -> None:
    parsed = urlparse(test_db_url)
    db_name = parsed.path.lstrip("/")
    admin_dsn = urlunparse(parsed._replace(scheme="postgresql", path="/postgres"))
    conn = await asyncpg.connect(admin_dsn)
    try:
        exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", db_name)
        if not exists:
            await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()


class FakeMailerService:
    def __init__(self) -> None:
        self.sent_emails: list[dict[str, str]] = []

    async def send_forgot_password_email(self, email: str, username: str, reset_url: str) -> None:
        self.sent_emails.append(
            {
                "email": email,
                "username": username,
                "reset_url": reset_url,
            }
        )


class FakeStorageService:
    def __init__(self) -> None:
        self.uploaded: dict[str, bytes] = {}

    async def upload(
        self,
        key: str,
        content: bytes,
        content_type: str | None = None,
        cache_control: str | None = None,
    ) -> None:
        self.uploaded[key] = content

    async def delete(self, key: str) -> None:
        self.uploaded.pop(key, None)


class FakeModerationProducer:
    def __init__(self) -> None:
        self.published: list[tuple[str, ModerationPayload]] = []

    async def publish(self, routing_key: str, payload: ModerationPayload) -> bool:
        self.published.append((routing_key, payload))
        return True


class FakeGeminiService:
    default_voice = "Orus"
    tts_model = "gemini-2.5-pro-preview-tts"

    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.tts_requests: list[tuple[str, str, str | None]] = []

    async def generate_structured_json(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: dict,
        model: str | None = None,
        temperature: float = 0.8,
    ) -> dict:
        self.prompts.append(prompt)
        return {
            "topic_label": "Crítica vs Comunidad",
            "hook_headline": "La prensa le dio 90. Los jugadores dicen otra cosa.",
            "hook_subheadline": "Debate real sin filtros en Pixel Reviews",
            "voice_direction": "Tono gamer enérgico y afilado",
            "full_narration": "La prensa especializada le puso un noventa cerrado, pero la comunidad opina distinto.",
            "slides": [
                {
                    "kind": "hook",
                    "eyebrow": "CRÍTICA VS JUGADORES",
                    "headline": "¿Obra maestra o inflado?",
                    "body": "Comparamos la nota oficial contra las reseñas reales.",
                    "badge": "DEBATE",
                    "image_url": "https://images.igdb.com/igdb/image/upload/t_1080p/sc1.webp",
                    "cover_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co1.webp",
                    "critic_score": 90,
                    "community_score": 3.8,
                    "quote_author": None,
                },
                {
                    "kind": "cta",
                    "eyebrow": "TU TURNO",
                    "headline": "Deja tu reseña sin filtro",
                    "body": "Entra en pixelreviews.app y vota.",
                    "badge": "PIXEL REVIEWS",
                    "image_url": None,
                    "cover_url": None,
                    "critic_score": None,
                    "community_score": None,
                    "quote_author": None,
                },
            ],
            "video_scenes": [
                {
                    "headline": "La prensa le dio 90/100",
                    "narration": "La prensa especializada le puso un noventa cerrado.",
                    "badge": "PRENSA 90",
                    "image_url": "https://images.igdb.com/igdb/image/upload/t_1080p/sc1.webp",
                    "cover_url": "https://images.igdb.com/igdb/image/upload/t_cover_big/co1.webp",
                    "critic_score": 90,
                    "community_score": 3.8,
                    "duration_seconds": 5.5,
                }
            ],
            "captions": {
                "tiktok": "¿Sobrevalorado o joya? #gaming #videojuegos",
                "instagram": "Debate abierto en la comunidad #videojuegos",
                "x_post": "Prensa 90 vs Jugadores 3.8★. ¿De qué lado estás?",
                "youtube_shorts": "Crítica vs Jugadores #shorts #gaming",
                "reddit_title": "¿Qué opinan realmente después de terminarlo?",
                "reddit_body": "Viendo la diferencia entre prensa y jugadores quería saber su experiencia.",
            },
        }

    async def generate_studio_tts(
        self,
        narration_text: str,
        voice_direction: str,
        voice_name: str | None = None,
    ) -> tuple[bytes, float]:
        from src.services.gemini.client import pcm_to_wav_bytes

        self.tts_requests.append((narration_text, voice_direction, voice_name))
        pcm_silence = b"\x00\x00" * 24000
        return pcm_to_wav_bytes(pcm_silence), 1.0

    async def translate_game_copy_to_spanish(
        self,
        title: str,
        description: str,
        storyline: str | None = None,
    ) -> dict[str, str | None]:
        return {
            "description_es": f"[ES] {description}",
            "storyline_es": f"[ES] {storyline}" if storyline else None,
        }


@pytest.fixture
def fake_mailer() -> FakeMailerService:
    return FakeMailerService()


@pytest.fixture
def fake_storage() -> FakeStorageService:
    return FakeStorageService()


@pytest.fixture
def fake_moderation_producer() -> FakeModerationProducer:
    return FakeModerationProducer()


@pytest.fixture
def fake_gemini() -> FakeGeminiService:
    return FakeGeminiService()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    test_db_url = get_test_database_url()
    await ensure_test_database_exists(test_db_url)

    test_engine = create_async_engine(test_db_url, poolclass=NullPool)
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def client(
    db_session: AsyncSession,
    fake_mailer: FakeMailerService,
    fake_storage: FakeStorageService,
    fake_moderation_producer: FakeModerationProducer,
    fake_gemini: FakeGeminiService,
) -> AsyncGenerator[AsyncClient]:
    async def override_get_session() -> AsyncGenerator[AsyncSession]:
        try:
            yield db_session
            await db_session.commit()
        except Exception:
            await db_session.rollback()
            raise

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_mailer_service] = lambda: fake_mailer
    app.dependency_overrides[get_storage_service] = lambda: fake_storage
    app.dependency_overrides[get_producer_service] = lambda: fake_moderation_producer
    app.dependency_overrides[get_gemini_service] = lambda: fake_gemini
    limiter.enabled = False

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    limiter.enabled = True
