from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.developers.models import Developer, DeveloperCreate


class DeveloperRepository:
    async def create(self, session: AsyncSession, data: DeveloperCreate) -> Developer:
        new_developer = Developer(**data.model_dump())
        session.add(new_developer)
        await session.flush()
        await session.refresh(new_developer)
        return new_developer

    async def get_by_slug(self, session: AsyncSession, slug: str) -> Developer | None:
        stmt = select(Developer).where(Developer.slug == slug)
        result = await session.exec(stmt)
        return result.first()


developer_repo = DeveloperRepository()
