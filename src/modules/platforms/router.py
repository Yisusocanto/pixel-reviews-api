from typing import Annotated

from fastapi import APIRouter, Query

from src.modules.platforms.dependencies import PlatformServiceDep
from src.modules.platforms.models import Platform
from src.modules.platforms.schemas import PlatformGamesPagination

router = APIRouter(prefix="/platforms", tags=["Platforms"])


@router.get("", response_model=list[Platform])
async def list_platforms(service: PlatformServiceDep):
    return await service.list_all()


@router.get("/{platform_slug}/games", response_model=PlatformGamesPagination)
async def list_platform_games(
    platform_slug: str,
    service: PlatformServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=50)] = 24,
):
    return await service.get_games_by_slug(platform_slug=platform_slug, page=page, limit=limit)
