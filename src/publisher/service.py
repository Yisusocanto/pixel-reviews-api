from sqlmodel.ext.asyncio.session import AsyncSession

from src.publisher.models import Publisher, PublisherCreate
from src.publisher.repository import publisher_repo


class PublisherService:
    async def find_or_create(self, session: AsyncSession, data: PublisherCreate) -> Publisher:
        existing_publisher = await publisher_repo.get_by_slug(session, data.slug)
        if existing_publisher:
            return existing_publisher

        new_publisher = await publisher_repo.create(session, data)
        return new_publisher


publisher_service = PublisherService()
