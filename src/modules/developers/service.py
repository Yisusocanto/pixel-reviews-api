from src.modules.developers.models import Developer, DeveloperCreate
from src.modules.developers.repository import DeveloperRepository


class DeveloperService:
    def __init__(self, repo: DeveloperRepository) -> None:
        self.repo = repo

    async def find_or_create(self, data: DeveloperCreate) -> Developer:
        existing_developer = await self.repo.get_by_slug(data.slug)
        if existing_developer:
            return existing_developer

        new_developer = await self.repo.create(data)
        return new_developer
