import uuid

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.stores.models import Store, StoreCreate


class StoreRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: StoreCreate) -> Store:
        new_store = Store(**data.model_dump())
        self.session.add(new_store)
        await self.session.flush()
        await self.session.refresh(new_store)
        return new_store

    async def get_by_id(self, store_id: uuid.UUID) -> Store | None:
        return await self.session.get(Store, store_id)

    async def get_by_slug(self, slug: str) -> Store | None:
        stmt = select(Store).where(Store.slug == slug)
        result = await self.session.exec(stmt)
        return result.first()

