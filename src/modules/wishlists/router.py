import uuid

from fastapi import APIRouter

from src.modules.auth.dependencies import CurrentUserDep
from src.modules.wishlists.dependencies import WishlistServiceDep
from src.modules.wishlists.models import WishlistCreate
from src.modules.wishlists.schemas import InUserWishlist

router = APIRouter(prefix="/wishlists", tags=["Wishlists"])


@router.post("/toggle", response_model=InUserWishlist)
async def toggle_game_wishlist(
    service: WishlistServiceDep, data: WishlistCreate, user: CurrentUserDep
):
    return await service.toggle(data, user.id)


@router.get("/game/{game_id}", response_model=InUserWishlist)
async def get_wishlist_item(service: WishlistServiceDep, game_id: uuid.UUID, user: CurrentUserDep):
    return await service.get_wishlist_item(game_id=game_id, user_id=user.id)
