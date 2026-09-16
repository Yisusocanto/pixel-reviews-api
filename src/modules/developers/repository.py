from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.developers.models import Developer, DeveloperCreate


class DeveloperRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: DeveloperCreate) -> Developer:
        new_developer = Developer(**data.model_dump())
        self.session.add(new_developer)
        await self.session.flush()
        await self.session.refresh(new_developer)
        return new_developer

    async def get_by_slug(self, slug: str) -> Developer | None:
        stmt = select(Developer).where(Developer.slug == slug)
        result = await self.session.exec(stmt)
        return result.first()
