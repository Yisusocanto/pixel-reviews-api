from typing import Annotated

from fastapi import Depends, Request

from src.services.cache.client import CacheService


def get_cache_service(request: Request) -> CacheService:
    redis_client = getattr(request.app.state, "redis", None)
    return CacheService(redis_client=redis_client)


CacheServiceDep = Annotated[CacheService, Depends(get_cache_service)]
