from typing import Annotated

from fastapi import Depends, Request

from src.core.settings import settings
from src.services.cache.dependencies import CacheServiceDep
from src.services.igdb.client import IgdbService


def get_igdb_service(request: Request, cache: CacheServiceDep) -> IgdbService:
    http_client = getattr(request.app.state, "http_client", None)
    return IgdbService(
        api_url=settings.IGDB_API_URL,
        auth_url=settings.TWITCH_AUTH_URL,
        client_id=settings.TWITCH_CLIENT_ID,
        client_secret=settings.TWITCH_CLIENT_SECRET,
        http_client=http_client,
        cache=cache,
    )


IgdbServiceDep = Annotated[IgdbService, Depends(get_igdb_service)]
