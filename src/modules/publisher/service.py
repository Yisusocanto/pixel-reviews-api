from src.modules.publisher.models import Publisher, PublisherCreate
from src.modules.publisher.repository import PublisherRepository


class PublisherService:
    def __init__(self, repo: PublisherRepository) -> None:
        self.repo = repo

    async def find_or_create(self, data: PublisherCreate) -> Publisher:
        existing_publisher = await self.repo.get_by_slug(data.slug)
        if existing_publisher:
            return existing_publisher

        new_publisher = await self.repo.create(data)
        return new_publisher
