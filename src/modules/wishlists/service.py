import uuid

from src.modules.wishlists.models import Wishlist, WishlistCreate
from src.modules.wishlists.repository import WishlistRepository
from src.modules.wishlists.schemas import InUserWishlist, WishlistPagination


class WishlistService:
    def __init__(self, repo: WishlistRepository):
        self.repo = repo

    async def toggle(self, data: WishlistCreate, user_id: uuid.UUID) -> InUserWishlist:
        existing_wishlist = await self.repo.get_wishlist_item(user_id=user_id, game_id=data.game_id)
        if not existing_wishlist:
            new_wishlist_item = await self.repo.create(data, user_id)
            return InUserWishlist(in_wishlist=True, wishlist_id=new_wishlist_item.id)

        await self.repo.remove(existing_wishlist)
        return InUserWishlist(in_wishlist=False, wishlist_id=None)

    async def get_wishlist_item(self, game_id: uuid.UUID, user_id: uuid.UUID):
        wishlist_item = await self.repo.get_wishlist_item(user_id=user_id, game_id=game_id)

        return InUserWishlist(
            in_wishlist=bool(wishlist_item), wishlist_id=wishlist_item.id if wishlist_item else None
        )

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
