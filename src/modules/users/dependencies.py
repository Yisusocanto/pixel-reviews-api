from typing import Annotated

from fastapi import Depends

from src.db.database import SessionDep
from src.modules.reviews.dependencies import ReviewServiceDep
from src.modules.users.repository import UserRepository
from src.modules.users.service import UserService
from src.modules.wishlists.dependencies import WishlistServiceDep
from src.services.dependencies import StorageServiceDep


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_user_service(
    repo: UserRepositoryDep,
    review_service: ReviewServiceDep,
    wishlist_service: WishlistServiceDep,
    storage: StorageServiceDep,
) -> UserService:
    return UserService(repo, review_service, wishlist_service, storage)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
