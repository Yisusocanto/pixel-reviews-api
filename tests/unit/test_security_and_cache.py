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
from src.services.rawg.client import RawgService


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
    user_id = uuid.uuid4()
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    access_payload = decode_token(access_token, expected_type=TOKEN_TYPE_ACCESS)
    assert access_payload["sub"] == str(user_id)
    assert access_payload["type"] == TOKEN_TYPE_ACCESS

    refresh_payload = decode_token(refresh_token, expected_type=TOKEN_TYPE_REFRESH)
    assert refresh_payload["sub"] == str(user_id)
    assert refresh_payload["type"] == TOKEN_TYPE_REFRESH


def test_jwt_rejects_wrong_token_type() -> None:
    user_id = uuid.uuid4()
    refresh_token = create_refresh_token(user_id)

    with pytest.raises(HTTPException) as exc_info:
        decode_token(refresh_token, expected_type=TOKEN_TYPE_ACCESS)

    assert exc_info.value.status_code == 401


def test_jwt_rejects_expired_token() -> None:
    user_id = uuid.uuid4()
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


async def test_rawg_search_uses_redis_cache_after_first_call() -> None:
    call_count = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            json={
                "count": 1,
                "results": [
                    {
                        "name": "Hollow Knight",
                        "slug": "hollow-knight",
                        "released": "2017-02-24",
                        "background_image": "https://example.com/hk.jpg",
                    }
                ],
            },
        )

    transport = httpx.MockTransport(mock_handler)
    fake_redis = InMemoryRedisFake()
    cache = CacheService(redis_client=fake_redis)

    async with httpx.AsyncClient(transport=transport) as http_client:
        service = RawgService(
            api_url="https://api.rawg.io/api",
            api_key="fake_key",
            http_client=http_client,
            cache=cache,
        )

        first_result = await service.search_games("Hollow Knight", page=1, limit=20)
        second_result = await service.search_games("hollow knight", page=1, limit=20)

    assert call_count == 1
    assert first_result is not None
    assert second_result is not None
    assert first_result.items[0].slug == "hollow-knight"
    assert second_result.items[0].slug == "hollow-knight"
