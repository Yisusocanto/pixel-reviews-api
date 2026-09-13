from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.lib.password_handler import hash_password
from src.users.models import User, UserCreate
from src.users.repository import user_repo
from src.users.schema import UserPagination


class UserService:
    async def create(self, session: AsyncSession, data: UserCreate) -> User:
        existing_username = await user_repo.get_by_username(session, data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with that username already exists.",
            )

        existing_email = await user_repo.get_by_email(session, data.email)
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

        return await user_repo.create(session, new_user)

    async def get_all(self, session: AsyncSession, page: int, limit: int) -> UserPagination:
        offset = (page - 1) * limit

        users = await user_repo.get_all(session, offset=offset, limit=limit)
        total = await user_repo.count_all(session)
        total_pages = (total - 1 + limit) // limit

        return UserPagination(items=users, page=page, total=total, total_pages=total_pages)

    async def get_user(self, session: AsyncSession, username: str) -> User:
        user = await user_repo.get_by_username(session, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user


user_service = UserService()
