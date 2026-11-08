import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.stores.models import Store, StoreCreate


class StoreRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: StoreCreate) -> Store:
        stmt = (
            pg_insert(Store)
            .values(
                id=uuid.uuid7(),
                name=data.name,
                slug=data.slug,
                domain=data.domain,
            )
            .on_conflict_do_nothing()
        )
        await self.session.exec(stmt)
        result = await self.session.exec(
            select(Store).where(Store.slug == data.slug).execution_options(populate_existing=True)
        )
        return result.one()

    async def get_by_id(self, store_id: uuid.UUID) -> Store | None:
        return await self.session.get(Store, store_id)

    async def get_by_slug(self, slug: str) -> Store | None:
        stmt = select(Store).where(Store.slug == slug)
        result = await self.session.exec(stmt)
        return result.first()
