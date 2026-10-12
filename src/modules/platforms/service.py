from src.modules.platforms.models import Platform, PlatformCreate
from src.modules.platforms.repository import PlatformRepository


class PlatformService:
    def __init__(self, repo: PlatformRepository):
        self.repo = repo

    async def find_or_create(self, data: PlatformCreate) -> Platform:
        existing_platform = await self.repo.get_by_slug(data.slug)
        if not existing_platform:
            new_platform = await self.repo.create(data)
            return new_platform

        return existing_platform
