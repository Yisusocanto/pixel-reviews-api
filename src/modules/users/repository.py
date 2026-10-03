import uuid
from collections.abc import Sequence

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.users.models import User, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_user(self, user_id: uuid.UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_username(self, username: str) -> User | None:
        consulta = select(User).where(User.username == username)
        result = await self.session.exec(consulta)
        return result.first()

    async def get_by_email(self, email: str) -> User | None:
        consulta = select(User).where(User.email == email)
        result = await self.session.exec(consulta)
        return result.first()

    async def get_all(self, offset: int, limit: int) -> Sequence[User]:
        stmt = select(User).offset(offset).limit(limit)
        result = await self.session.exec(stmt)
        return result.all()

    async def count_all(self) -> int:
        stmt = select(func.count(User.id))
        result = await self.session.exec(stmt)
        total = result.first()
        return total if total is not None else 0

    async def update(self, user: User, new_data: UserUpdate) -> User:
        data = new_data.model_dump(exclude_unset=True)
        user.sqlmodel_update(data)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user
