import uuid

from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.wishlists.models import Wishlist, WishlistCreate


class WishlistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: WishlistCreate, user_id: uuid.UUID) -> Wishlist:
        new_wishlist_item = Wishlist(**data.model_dump(), user_id=user_id)
        self.session.add(new_wishlist_item)
        await self.session.flush()
        wishlist = await self.get_by_id(new_wishlist_item.id)
        return wishlist or new_wishlist_item

    async def get_by_id(self, wishlist_id: uuid.UUID) -> Wishlist | None:
        stmt = (
            select(Wishlist)
            .where(Wishlist.id == wishlist_id)
            .options(
                selectinload(Wishlist.game),
                selectinload(Wishlist.user),
            )
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def remove(self, wishlist: Wishlist) -> Wishlist:
        await self.session.delete(wishlist)
        return wishlist

    async def get_all(self, offset: int, limit: int, user_id: uuid.UUID) -> list[Wishlist]:
        stmt = (
            select(Wishlist)
            .where(Wishlist.user_id == user_id)
            .offset(offset)
            .limit(limit)
            .options(
                selectinload(Wishlist.game),
                selectinload(Wishlist.user),
            )
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def count_all(
        self, user_id: uuid.UUID | None = None, game_id: uuid.UUID | None = None
    ) -> int:
        stmt = select(func.count(Wishlist.id))
        if user_id:
            stmt = stmt.where(Wishlist.user_id == user_id)
        if game_id:
            stmt = stmt.where(Wishlist.game == game_id)

        result = await self.session.exec(stmt)
        total = result.first()
        return total if total is not None else 0
