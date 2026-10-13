import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.publisher.models import Publisher, PublisherCreate


class PublisherRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: PublisherCreate) -> Publisher:
        # Atomic upsert: concurrent requests may try to insert the same RAWG entity.
        stmt = (
            pg_insert(Publisher)
            .values(**data.model_dump(), id=uuid.uuid4())
            .on_conflict_do_nothing()
        )
        await self.session.exec(stmt)
        result = await self.session.exec(
            select(Publisher)
            .where(Publisher.rawg_id == data.rawg_id)
            .execution_options(populate_existing=True)
        )
        return result.one()

    async def get_by_slug(self, slug: str) -> Publisher | None:
        stmt = select(Publisher).where(Publisher.slug == slug)
        result = await self.session.exec(stmt)
        return result.first()
