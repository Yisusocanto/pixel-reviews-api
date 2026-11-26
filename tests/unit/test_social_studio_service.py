import uuid
from datetime import UTC, datetime

from src.modules.games.models import Game
from src.modules.social_studio.schemas import (
    SocialAngle,
    SocialGenerateRequest,
    SocialLanguage,
    StudioTtsRequest,
)
from src.modules.social_studio.service import SocialStudioService, to_hd_jpg_url
from tests.conftest import FakeGeminiService, FakeStorageService


class StubSocialRepo:
    def __init__(self, game: Game) -> None:
        self.game = game

    async def get_games_with_community_stats(self, limit: int = 20):
        return [(self.game, 4.1, 14)]

    async def get_hidden_gem_games(self, limit: int = 12):
        return [(self.game, 4.6, 3)]

    async def get_most_anticipated_games(self, limit: int = 12):
        return [(self.game, 29)]

    async def get_featured_reviews(self, limit: int = 15):
        return []

    async def get_game_by_slug_with_stats(self, slug: str):
        if slug == self.game.slug:
            return (self.game, 4.1, 14)
        return None

    async def get_review_by_id(self, review_id: uuid.UUID):
        return None


def _sample_game() -> Game:
    return Game(
        id=uuid.uuid7(),
        title="Hollow Knight",
        slug="hollow-knight",
        igdb_id=14593,
        release_date=datetime(2017, 2, 24, tzinfo=UTC),
        image_url="https://images.igdb.com/igdb/image/upload/t_thumb/co1rgi.webp",
        background_image="https://images.igdb.com/igdb/image/upload/t_720p/sc6abc.webp",
        screenshots=["https://images.igdb.com/igdb/image/upload/t_720p/sc6abc.webp"],
        critic_score=90,
        description="A classic 2D action adventure across Hallownest.",
    )


async def test_to_hd_jpg_url_rewrites_igdb_size_and_format() -> None:
    converted = to_hd_jpg_url(
        "https://images.igdb.com/igdb/image/upload/t_thumb/co1rgi.webp",
        "t_cover_big_2x",
    )
    assert converted == "https://images.igdb.com/igdb/image/upload/t_cover_big_2x/co1rgi.jpg"


async def test_social_studio_service_generates_pack_and_tts() -> None:
    game = _sample_game()
    repo = StubSocialRepo(game)
    gemini = FakeGeminiService()
    storage = FakeStorageService()
    service = SocialStudioService(repo=repo, gemini=gemini, storage=storage)

    candidates = await service.list_candidates(SocialAngle.CRITIC_VS_PLAYERS, limit=5)
    assert len(candidates.items) == 1
    assert candidates.items[0].game_slug == "hollow-knight"
    assert candidates.items[0].cover_url.endswith(".jpg")

    pack = await service.generate_pack(
        SocialGenerateRequest(
            angle=SocialAngle.CRITIC_VS_PLAYERS,
            language=SocialLanguage.ES,
            game_slug="hollow-knight",
        )
    )
    assert pack.hook_headline
    assert len(pack.slides) == 2
    assert pack.slides[0].image_url == "https://images.igdb.com/igdb/image/upload/t_1080p/sc1.jpg"
    assert len(pack.video_scenes) == 1

    tts = await service.synthesize_voiceover(
        StudioTtsRequest(
            narration=pack.full_narration,
            voice_direction=pack.voice_direction,
            voice_name="Orus",
        )
    )
    assert tts.audio_data_url.startswith("data:audio/wav;base64,")
    assert tts.duration_seconds == 1.0
    assert len(storage.uploaded) == 1
