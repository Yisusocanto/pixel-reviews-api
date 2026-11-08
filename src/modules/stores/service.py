from src.modules.stores.models import Store, StoreCreate
from src.modules.stores.repository import StoreRepository


class StoreService:
    def __init__(self, repo: StoreRepository):
        self.repo = repo

    async def create_or_find(self, data: StoreCreate) -> tuple[Store, str | None]:
        existing_store = await self.repo.get_by_slug(data.slug)
        if existing_store:
            return existing_store, data.url

        store = await self.repo.create(data)
        return store, data.url
