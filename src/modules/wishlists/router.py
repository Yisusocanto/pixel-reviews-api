import uuid

from fastapi import APIRouter

from src.modules.auth.dependencies import CurrentUserDep
from src.modules.wishlists.dependencies import WishlistServiceDep
from src.modules.wishlists.models import WishlistCreate
from src.modules.wishlists.schemas import WishlistResponse

router = APIRouter(prefix="/wishlists", tags=["Wishlists"])


@router.post("", response_model=WishlistResponse)
async def create(service: WishlistServiceDep, data: WishlistCreate, user: CurrentUserDep):
    return await service.create(data, user.id)


@router.delete("/{wishlist_id}", response_model=WishlistResponse)
async def remove(service: WishlistServiceDep, wishlist_id: uuid.UUID, user: CurrentUserDep):
    return await service.remove(wishlist_id, user.id)
