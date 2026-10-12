import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.platforms.models import Platform, PlatformCreate


class PlatformRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: PlatformCreate) -> Platform:
        stmt = (
            pg_insert(Platform)
            .values(**data.model_dump(), id=uuid.uuid4())
            .on_conflict_do_nothing()
        )
        await self.session.exec(stmt)
        result = await self.session.exec(
            select(Platform)
            .where(Platform.slug == data.slug)
            .execution_options(populate_existing=True)
        )
        return result.one()

    async def get_by_id(self, platform_id: uuid.UUID) -> Platform | None:
        return await self.session.get(Platform, platform_id)

    async def get_by_slug(self, slug: str) -> Platform | None:
        stmt = select(Platform).where(Platform.slug == slug)
        result = await self.session.exec(stmt)
        return result.first()
