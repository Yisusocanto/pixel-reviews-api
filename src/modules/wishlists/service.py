import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.modules.wishlists.models import Wishlist, WishlistCreate
from src.modules.wishlists.repository import WishlistRepository
from src.modules.wishlists.schemas import WishlistPagination


class WishlistService:
    def __init__(self, repo: WishlistRepository):
        self.repo = repo

    async def create(self, data: WishlistCreate, user_id: uuid.UUID) -> Wishlist:
        try:
            new_wishlist_item = await self.repo.create(data, user_id)
            return new_wishlist_item
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Game already in you wishlist"
            )

    async def remove(self, wishlist_id: uuid.UUID, user_id: uuid.UUID) -> Wishlist:
        wishlist = await self.repo.get_by_id(wishlist_id)
        if not wishlist:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")

        if wishlist.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed")

        return await self.repo.remove(wishlist)

    async def get_all(self, page: int, limit: int, user_id: uuid.UUID) -> WishlistPagination:
        offset = (page - 1) * limit
        wishlists = await self.repo.get_all(offset, limit, user_id)
        total = await self.repo.count_all(user_id=user_id)
        total_pages = (total - 1 + limit) // limit

        return WishlistPagination(
            items=wishlists,
            total_pages=total_pages,
            total=total,
            page=page,
        )
