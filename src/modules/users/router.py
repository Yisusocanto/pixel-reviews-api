from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, File, Query, UploadFile

from src.modules.auth.dependencies import CurrentUserDep, OptionalCurrentUserDep
from src.modules.likes.dependencies import LikeServiceDep
from src.modules.reviews.dependencies import ReviewServiceDep
from src.modules.reviews.schemas import ReviewPagination
from src.modules.users.dependencies import UserServiceDep
from src.modules.users.models import UserResponse, UserUpdate
from src.modules.users.schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdatePasswordRequest,
    UserPagination,
    UserStats,
)
from src.modules.users.service import MAX_PROFILE_PHOTO_BYTES
from src.modules.wishlists.schemas import WishlistPagination

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserPagination)
async def get_all(
    service: UserServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await service.get_all(page, limit)


@router.patch("", response_model=UserResponse)
async def update(service: UserServiceDep, data: UserUpdate, user: CurrentUserDep):
    return await service.update(data, user.id)


@router.patch("/update-password", response_model=UserResponse)
async def update_password(
    service: UserServiceDep, data: UpdatePasswordRequest, user: CurrentUserDep
):
    return await service.update_password(user, data.old_password, data.new_password)


@router.post("/forgot-password", response_model=dict[str, str])
async def forgot_password(
    service: UserServiceDep, data: ForgotPasswordRequest, bg_tasks: BackgroundTasks
):
    return await service.forgot_password(data.email, bg_tasks)


@router.post("/reset-password", response_model=dict[str, str])
async def reset_password(service: UserServiceDep, data: ResetPasswordRequest):
    return await service.reset_password(data.token, data.new_password)


@router.get("/{username}", response_model=UserResponse)
async def get_user(username: str, service: UserServiceDep):
    return await service.get_user(username)


@router.post("/profile-photo", response_model=UserResponse)
async def upload_profile_photo(
    service: UserServiceDep, user: CurrentUserDep, file: Annotated[UploadFile, File()]
):
    content = await file.read(MAX_PROFILE_PHOTO_BYTES + 1)
    return await service.update_profile_photo(user, content, file.content_type)


@router.get("/{username}/stats", response_model=UserStats)
async def user_stats(
    service: UserServiceDep,
    username: str,
    review_service: ReviewServiceDep,
    like_service: LikeServiceDep,
):
    user = await service.get_user(username)
    user_review_stats = await review_service.user_stats(user.id)
    user_likes = await like_service.count_user_likes(user.id)
    return UserStats(**user_review_stats.model_dump(), total_likes=user_likes)


@router.get("/{username}/reviews", response_model=ReviewPagination)
async def user_reviews(
    service: UserServiceDep,
    username: str,
    optional_current_user: OptionalCurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    current_user_id = optional_current_user.id if optional_current_user else None
    return await service.get_user_reviews(
        page=page, limit=limit, username=username, current_user_id=current_user_id
    )


@router.get("/{username}/wishlist", response_model=WishlistPagination)
async def user_wishlist(
    service: UserServiceDep,
    username: str,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await service.user_wishlist(page, limit, username)
