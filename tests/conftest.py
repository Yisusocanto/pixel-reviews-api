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
from src.modules.comments.models import Comment
from src.modules.developers.models import Developer
from src.modules.games.models import Game
from src.modules.genres.models import Genre
from src.modules.likes.models import Like
from src.modules.password_reset_tokens.models import PasswordResetToken
from src.modules.platforms.models import Platform
from src.modules.publisher.models import Publisher
from src.modules.reviews.models import Review
from src.modules.stores.models import Store
from src.modules.users.models import User
from src.modules.wishlists.models import Wishlist
from src.services.mailer.dependencies import get_mailer_service
from src.services.storage.dependencies import get_storage_service

REGISTERED_MODELS = (
    Comment,
    Developer,
    Game,
    Genre,
    Like,
    PasswordResetToken,
    Platform,
    Publisher,
    Review,
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


@pytest.fixture
def fake_mailer() -> FakeMailerService:
    return FakeMailerService()


@pytest.fixture
def fake_storage() -> FakeStorageService:
    return FakeStorageService()


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
    limiter.enabled = False

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    limiter.enabled = True
