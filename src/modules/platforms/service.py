from fastapi import HTTPException, status

from src.modules.platforms.models import Platform, PlatformCreate
from src.modules.platforms.repository import PlatformRepository
from src.modules.platforms.schemas import PlatformGamesPagination


class PlatformService:
    def __init__(self, repo: PlatformRepository):
        self.repo = repo

    async def find_or_create(self, data: PlatformCreate) -> Platform:
        existing_platform = await self.repo.get_by_slug(data.slug)
        if not existing_platform:
            new_platform = await self.repo.create(data)
            return new_platform

        return existing_platform

    async def list_all(self) -> list[Platform]:
        return list(await self.repo.list_all())

    async def get_games_by_slug(
        self, platform_slug: str, page: int = 1, limit: int = 24
    ) -> PlatformGamesPagination:
        platform = await self.repo.get_by_slug(platform_slug)
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Platform not found",
            )
        offset = (page - 1) * limit
        games = await self.repo.list_games_by_platform(platform.id, offset=offset, limit=limit)
        total = await self.repo.count_games_by_platform(platform.id)
        total_pages = (total - 1 + limit) // limit if total > 0 else 0
        return PlatformGamesPagination(
            platform=platform,
            items=list(games),
            page=page,
            total=total,
            total_pages=total_pages,
        )
