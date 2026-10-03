import uuid

from fastapi import HTTPException, status

from src.lib.password_handler import hash_password
from src.modules.reviews.service import ReviewService
from src.modules.users.models import User, UserCreate, UserUpdate
from src.modules.users.repository import UserRepository
from src.modules.users.schemas import UserPagination
from src.modules.wishlists.schemas import WishlistPagination
from src.modules.wishlists.service import WishlistService


class UserService:
    def __init__(
        self, repo: UserRepository, review_service: ReviewService, wishlist_service: WishlistService
    ) -> None:
        self.repo = repo
        self.review_service = review_service
        self.wishlist_service = wishlist_service

    async def create(self, data: UserCreate) -> User:
        existing_username = await self.repo.get_by_username(data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with that username already exists.",
            )

        existing_email = await self.repo.get_by_email(data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with that email already exists.",
            )

        hashed_password = await hash_password(data.password)
        new_user = User(
            email=data.email,
            username=data.username,
            bio=data.bio,
            hashed_password=hashed_password,
        )

        return await self.repo.create(new_user)

    async def update(self, data: UserUpdate, user_id: uuid.UUID) -> User:
        user = await self.repo.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
            )

        updated_user = await self.repo.update(user, data)
        return updated_user

    async def get_all(self, page: int, limit: int) -> UserPagination:
        offset = (page - 1) * limit

        users = await self.repo.get_all(offset=offset, limit=limit)
        total = await self.repo.count_all()
        total_pages = (total - 1 + limit) // limit if total > 0 else 0

        return UserPagination(items=users, page=page, total=total, total_pages=total_pages)

    async def get_user(self, username: str) -> User:
        user = await self.repo.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user

    async def get_user_reviews(
        self, page: int, limit: int, username: str, current_user_id: uuid.UUID | None = None
    ):
        user = await self.get_user(username)
        return await self.review_service.get_all(
            page, limit, user_id=user.id, current_user_id=current_user_id
        )

    async def user_wishlist(self, page: int, limit: int, username: str) -> WishlistPagination:
        user = await self.get_user(username)
        wishlist = await self.wishlist_service.get_all(page, limit, user.id)
        return wishlist
