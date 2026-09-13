import uuid
from collections.abc import Sequence

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.users.models import User


class UserRepository:
    async def create(self, session: AsyncSession, user: User) -> User:
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user

    async def get_user(self, session: AsyncSession, user_id: uuid.UUID) -> User | None:
        return await session.get(User, user_id)

    async def get_by_username(self, session: AsyncSession, username: str) -> User | None:
        consulta = select(User).where(User.username == username)
        result = await session.exec(consulta)
        return result.first()

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        consulta = select(User).where(User.email == email)
        result = await session.exec(consulta)
        return result.first()

    async def get_all(self, session: AsyncSession, offset: int, limit: int) -> Sequence[User]:
        stmt = select(User).offset(offset).limit(limit)
        result = await session.exec(stmt)
        return result.all()

    async def count_all(self, session: AsyncSession) -> int:
        stmt = select(func.count(User.id))
        result = await session.exec(stmt)
        total = result.first()
        return total if total is not None else 0


user_repo = UserRepository()
