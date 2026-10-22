from typing import Annotated

from fastapi import Depends, Request

from src.core.settings import settings
from src.services.cache.dependencies import CacheServiceDep
from src.services.rawg.client import RawgService


def get_rawg_service(request: Request, cache: CacheServiceDep) -> RawgService:
    http_client = getattr(request.app.state, "http_client", None)
    return RawgService(
        api_url=settings.API_RAWG_URL,
        api_key=settings.API_RAWG_KEY,
        http_client=http_client,
        cache=cache,
    )


RawgServiceDep = Annotated[RawgService, Depends(get_rawg_service)]
