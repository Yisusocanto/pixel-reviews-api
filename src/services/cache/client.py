import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger("cache_service")


class CacheService:
    def __init__(self, redis_client: Redis | None = None) -> None:
        self.redis = redis_client

    async def get(self, key: str) -> str | None:
        if self.redis is None:
            return None
        try:
            return await self.redis.get(key)
        except RedisError as exc:
            logger.warning("[CACHE] Failed to read key '%s': %s", key, exc)
            return None

    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        if self.redis is None:
            return
        try:
            await self.redis.set(key, value, ex=ttl_seconds)
        except RedisError as exc:
            logger.warning("[CACHE] Failed to write key '%s': %s", key, exc)

    async def delete(self, key: str) -> None:
        if self.redis is None:
            return
        try:
            await self.redis.delete(key)
        except RedisError as exc:
            logger.warning("[CACHE] Failed to delete key '%s': %s", key, exc)
