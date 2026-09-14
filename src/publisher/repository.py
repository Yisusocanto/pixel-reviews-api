from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.publisher.models import Publisher, PublisherCreate


class PublisherRepository:
    async def create(self, session: AsyncSession, data: PublisherCreate) -> Publisher:
        new_publisher = Publisher(**data.model_dump())
        session.add(new_publisher)
        await session.flush()
        await session.refresh(new_publisher)
        return new_publisher

    async def get_by_slug(self, session: AsyncSession, slug: str) -> Publisher | None:
        stmt = select(Publisher).where(Publisher.slug == slug)
        result = await session.exec(stmt)
        return result.first()


publisher_repo = PublisherRepository()
