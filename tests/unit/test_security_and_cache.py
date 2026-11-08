import uuid
from datetime import timedelta

import httpx
import pytest
from fastapi import HTTPException
from redis.exceptions import RedisError

from src.lib.password_handler import check_password, hash_password
from src.modules.auth.security import (
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    create_token,
    decode_token,
)
from src.services.cache.client import CacheService
from src.services.igdb.client import IgdbService


class InMemoryRedisFake:
    def __init__(self, should_fail: bool = False) -> None:
        self.store: dict[str, str] = {}
        self.should_fail = should_fail

    async def get(self, key: str) -> str | None:
        if self.should_fail:
            raise RedisError("Simulated connection failure")
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        if self.should_fail:
            raise RedisError("Simulated connection failure")
        self.store[key] = value

    async def delete(self, key: str) -> None:
        if self.should_fail:
            raise RedisError("Simulated connection failure")
        self.store.pop(key, None)


async def test_password_hash_and_verify() -> None:
    raw = "MySecurePass123!"
    hashed = await hash_password(raw)

    assert hashed != raw
    assert await check_password(raw, hashed) is True
    assert await check_password("WrongPassword", hashed) is False


def test_jwt_access_and_refresh_token_lifecycle() -> None:
    user_id = uuid.uuid7()
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    access_payload = decode_token(access_token, expected_type=TOKEN_TYPE_ACCESS)
    assert access_payload["sub"] == str(user_id)
    assert access_payload["type"] == TOKEN_TYPE_ACCESS

    refresh_payload = decode_token(refresh_token, expected_type=TOKEN_TYPE_REFRESH)
    assert refresh_payload["sub"] == str(user_id)
    assert refresh_payload["type"] == TOKEN_TYPE_REFRESH


def test_jwt_rejects_wrong_token_type() -> None:
    user_id = uuid.uuid7()
    refresh_token = create_refresh_token(user_id)

    with pytest.raises(HTTPException) as exc_info:
        decode_token(refresh_token, expected_type=TOKEN_TYPE_ACCESS)

    assert exc_info.value.status_code == 401


def test_jwt_rejects_expired_token() -> None:
    user_id = uuid.uuid7()
    expired_token = create_token(
        subject=user_id,
        token_type=TOKEN_TYPE_ACCESS,
        expires_delta=timedelta(seconds=-10),
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_token(expired_token, expected_type=TOKEN_TYPE_ACCESS)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token has expired"


async def test_cache_service_resilience_on_redis_failure() -> None:
    failing_redis = InMemoryRedisFake(should_fail=True)
    cache = CacheService(redis_client=failing_redis)

    await cache.set("test:key", "value", ttl_seconds=60)
    result = await cache.get("test:key")
    await cache.delete("test:key")

    assert result is None


async def test_igdb_search_uses_redis_cache_and_oauth_token() -> None:
    oauth_calls = 0
    games_calls = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal oauth_calls, games_calls
        if "oauth2/token" in str(request.url):
            oauth_calls += 1
            return httpx.Response(200, json={"access_token": "fake_igdb_token", "expires_in": 3600})
        if request.url.path.endswith("/games/count"):
            return httpx.Response(200, json={"count": 1})
        games_calls += 1
        return httpx.Response(
            200,
            json=[
                {
                    "id": 119133,
                    "name": "Elden Ring",
                    "slug": "elden-ring",
                    "first_release_date": 1645747200,
                    "aggregated_rating": 96.9,
                    "cover": {"image_id": "co4jni"},
                    "artworks": [{"image_id": "ar3m1o"}],
                }
            ],
        )

    transport = httpx.MockTransport(mock_handler)
    fake_redis = InMemoryRedisFake()
    cache = CacheService(redis_client=fake_redis)

    async with httpx.AsyncClient(transport=transport) as http_client:
        service = IgdbService(
            api_url="https://api.igdb.com/v4",
            auth_url="https://id.twitch.tv/oauth2/token",
            client_id="fake_client",
            client_secret="fake_secret",
            http_client=http_client,
            cache=cache,
        )

        first_result = await service.search_games("Elden Ring", page=1, limit=20)
        second_result = await service.search_games("elden ring", page=1, limit=20)

    assert oauth_calls == 1
    assert games_calls == 1
    assert first_result is not None
    assert second_result is not None
    assert first_result.items[0].slug == "elden-ring"
    assert first_result.items[0].critic_score == 97
    assert (
        first_result.items[0].image_url
        == "https://images.igdb.com/igdb/image/upload/t_cover_big_2x/co4jni.webp"
    )
    assert second_result.items[0].slug == "elden-ring"


async def test_igdb_get_game_details_parses_enriched_fields() -> None:
    def mock_handler(request: httpx.Request) -> httpx.Response:
        if "oauth2/token" in str(request.url):
            return httpx.Response(200, json={"access_token": "fake_igdb_token", "expires_in": 3600})
        return httpx.Response(
            200,
            json=[
                {
                    "id": 119133,
                    "name": "Elden Ring",
                    "slug": "elden-ring",
                    "summary": "Action RPG in the Lands Between.",
                    "storyline": "The Elden Ring was shattered.",
                    "first_release_date": 1645747200,
                    "aggregated_rating": 96.9,
                    "aggregated_rating_count": 10,
                    "url": "https://www.igdb.com/games/elden-ring",
                    "cover": {"image_id": "co4jni"},
                    "artworks": [{"image_id": "ar3m1o"}],
                    "screenshots": [{"image_id": "scagdo"}],
                    "videos": [{"name": "Launch Trailer", "video_id": "qqiC88f9ogU"}],
                    "game_modes": [{"name": "Single player"}, {"name": "Co-operative"}],
                    "themes": [{"name": "Fantasy"}, {"name": "Open world"}],
                    "player_perspectives": [{"name": "Third person"}],
                    "genres": [{"name": "Role-playing (RPG)", "slug": "role-playing-rpg"}],
                    "platforms": [{"name": "PC (Microsoft Windows)", "slug": "win"}],
                    "involved_companies": [
                        {
                            "developer": True,
                            "publisher": False,
                            "company": {"id": 1012, "name": "FromSoftware", "slug": "fromsoftware"},
                        },
                        {
                            "developer": False,
                            "publisher": True,
                            "company": {
                                "id": 248,
                                "name": "Bandai Namco",
                                "slug": "bandai-namco",
                            },
                        },
                    ],
                    "websites": [
                        {"url": "https://store.steampowered.com/app/1245620"},
                        {"url": "https://www.bandainamcoent.com/games/elden-ring"},
                        {"url": "https://twitter.com/ELDENRING"},
                    ],
                }
            ],
        )

    transport = httpx.MockTransport(mock_handler)
    fake_redis = InMemoryRedisFake()
    cache = CacheService(redis_client=fake_redis)

    async with httpx.AsyncClient(transport=transport) as http_client:
        service = IgdbService(
            api_url="https://api.igdb.com/v4",
            auth_url="https://id.twitch.tv/oauth2/token",
            client_id="fake_client",
            client_secret="fake_secret",
            http_client=http_client,
            cache=cache,
        )
        detail = await service.get_game_details("elden-ring")

    assert detail is not None
    assert detail.igdb_id == 119133
    assert detail.storyline == "The Elden Ring was shattered."
    assert detail.critic_score == 97
    assert detail.critic_score_count == 10
    assert detail.trailer_youtube_id == "qqiC88f9ogU"
    assert detail.trailer_title == "Launch Trailer"
    assert detail.game_modes == ["Single player", "Co-operative"]
    assert detail.themes == ["Fantasy", "Open world"]
    assert detail.player_perspectives == ["Third person"]
    assert detail.website == "https://www.bandainamcoent.com/games/elden-ring"
    assert len(detail.stores) == 1
    assert detail.stores[0].slug == "steam"
    assert detail.stores[0].url == "https://store.steampowered.com/app/1245620"
