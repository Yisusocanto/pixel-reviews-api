from typing import Annotated

from fastapi import Depends

from src.core.settings import settings
from src.services.rawg.client import RawgService


def get_rawg_service() -> RawgService:
    return RawgService(api_url=settings.API_RAWG_URL, api_key=settings.API_RAWG_KEY)


RawgServiceDep = Annotated[RawgService, Depends(get_rawg_service)]
