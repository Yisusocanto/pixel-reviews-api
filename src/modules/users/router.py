from typing import Annotated

from fastapi import APIRouter, Query

from src.modules.reviews.schemas import ReviewPagination
from src.modules.users.dependencies import UserServiceDep
from src.modules.users.models import UserResponse
from src.modules.users.schema import UserPagination
from src.modules.wishlists.schemas import WishlistPagination

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserPagination)
async def get_all(
    service: UserServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await service.get_all(page, limit)


@router.get("/{username}", response_model=UserResponse)
async def get_user(username: str, service: UserServiceDep):
    return await service.get_user(username)


@router.get("/{username}/reviews", response_model=ReviewPagination)
async def user_reviews(
    service: UserServiceDep,
    username: str,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await service.get_user_reviews(page=page, limit=limit, username=username)


@router.get("/{username}/wishlist", response_model=WishlistPagination)
async def user_wishlist(
    service: UserServiceDep,
    username: str,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await service.user_wishlist(page, limit, username)
