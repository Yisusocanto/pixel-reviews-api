from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.wishlists.repository import WishlistRepository
from src.modules.wishlists.service import WishlistService


def get_wishlist_repo(session: SessionDep) -> WishlistRepository:
    return WishlistRepository(session)


WishlistRepositoryDep = Annotated[WishlistRepository, Depends(get_wishlist_repo)]


def get_wishlist_service(repo: WishlistRepositoryDep) -> WishlistService:
    return WishlistService(repo)


WishlistServiceDep = Annotated[WishlistService, Depends(get_wishlist_service)]
