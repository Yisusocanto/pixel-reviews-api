from sqlmodel.ext.asyncio.session import AsyncSession

from src.developers.models import Developer, DeveloperCreate
from src.developers.repository import developer_repo


class DeveloperService:
    async def find_or_create(self, session: AsyncSession, data: DeveloperCreate) -> Developer:
        existing_developer = await developer_repo.get_by_slug(session, data.slug)
        if existing_developer:
            return existing_developer

        new_developer = await developer_repo.create(session, data)
        return new_developer


developer_service = DeveloperService()
