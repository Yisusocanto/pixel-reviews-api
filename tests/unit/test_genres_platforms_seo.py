import uuid

import pytest
from fastapi import HTTPException

from src.modules.games.models import Game
from src.modules.genres.models import Genre
from src.modules.genres.service import GenreService
from src.modules.platforms.models import Platform
from src.modules.platforms.service import PlatformService


class StubGenreRepo:
    def __init__(self, genre: Genre, game: Game) -> None:
        self.genre = genre
        self.game = game

    async def get_by_slug(self, slug: str) -> Genre | None:
        return self.genre if slug == self.genre.slug else None

    async def list_all(self) -> list[Genre]:
        return [self.genre]

    async def list_games_by_genre(self, genre_id: uuid.UUID, offset: int, limit: int):
        return [self.game] if offset == 0 else []

    async def count_games_by_genre(self, genre_id: uuid.UUID) -> int:
        return 1


class StubPlatformRepo:
    def __init__(self, platform: Platform, game: Game) -> None:
        self.platform = platform
        self.game = game

    async def get_by_slug(self, slug: str) -> Platform | None:
        return self.platform if slug == self.platform.slug else None

    async def list_all(self) -> list[Platform]:
        return [self.platform]

    async def list_games_by_platform(self, platform_id: uuid.UUID, offset: int, limit: int):
        return [self.game] if offset == 0 else []

    async def count_games_by_platform(self, platform_id: uuid.UUID) -> int:
        return 1


async def test_genre_and_platform_seo_services_paginate_and_handle_missing() -> None:
    genre = Genre(id=uuid.uuid7(), name="Role-playing (RPG)", slug="role-playing-rpg")
    platform = Platform(id=uuid.uuid7(), name="PC (Microsoft Windows)", slug="win")
    game = Game(
        id=uuid.uuid7(),
        title="Elden Ring",
        slug="elden-ring",
        igdb_id=119133,
        image_url="https://images.igdb.com/igdb/image/upload/t_cover_big/co4jni.webp",
        description="Action RPG",
    )

    genre_service = GenreService(repo=StubGenreRepo(genre, game))
    genres = await genre_service.list_all()
    assert len(genres) == 1

    genre_page = await genre_service.get_games_by_slug("role-playing-rpg", page=1, limit=24)
    assert genre_page.total == 1
    assert genre_page.genre.slug == "role-playing-rpg"
    assert genre_page.items[0].slug == "elden-ring"

    with pytest.raises(HTTPException) as exc_info:
        await genre_service.get_games_by_slug("unknown-genre")
    assert exc_info.value.status_code == 404

    platform_service = PlatformService(repo=StubPlatformRepo(platform, game))
    platform_page = await platform_service.get_games_by_slug("win", page=1, limit=24)
    assert platform_page.total == 1
    assert platform_page.platform.slug == "win"
