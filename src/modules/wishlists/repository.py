import uuid
from collections.abc import Sequence

from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql.expression import col

from src.modules.wishlists.models import Wishlist


class WishlistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, wishlist_item: Wishlist) -> Wishlist:
        self.session.add(wishlist_item)
        await self.session.flush()
        wishlist = await self.get_by_id(wishlist_item.id)
        return wishlist or wishlist_item

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

    async def get_wishlist_item(self, user_id: uuid.UUID, game_id: uuid.UUID) -> Wishlist | None:
        stmt = select(Wishlist).where(Wishlist.game_id == game_id, Wishlist.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def remove(self, wishlist: Wishlist) -> Wishlist:
        await self.session.delete(wishlist)
        return wishlist

    async def get_all(self, offset: int, limit: int, user_id: uuid.UUID) -> Sequence[Wishlist]:
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
        stmt = select(func.count(col(Wishlist.id)))
        if user_id:
            stmt = stmt.where(Wishlist.user_id == user_id)
        if game_id:
            stmt = stmt.where(Wishlist.game == game_id)

        result = await self.session.exec(stmt)
        total = result.first()
        return total if total is not None else 0
