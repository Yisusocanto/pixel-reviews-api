from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.publisher.models import Publisher, PublisherCreate


class PublisherRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, data: PublisherCreate) -> Publisher:
        new_publisher = Publisher(**data.model_dump())
        self.session.add(new_publisher)
        await self.session.flush()
        await self.session.refresh(new_publisher)
        return new_publisher

    async def get_by_slug(self, slug: str) -> Publisher | None:
        stmt = select(Publisher).where(Publisher.slug == slug)
        result = await self.session.exec(stmt)
        return result.first()
