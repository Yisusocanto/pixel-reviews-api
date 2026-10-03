import uuid

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.likes.models import Like


class LikeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, review_id: uuid.UUID, user_id: uuid.UUID) -> Like:
        new_like = Like(review_id=review_id, user_id=user_id)
        self.session.add(new_like)
        await self.session.flush()
        return new_like

    async def remove(self, like: Like) -> None:
        await self.session.delete(like)
        await self.session.flush()

    async def get_user_review_like(self, user_id: uuid.UUID, review_id: uuid.UUID) -> Like | None:
        stmt = select(Like).where(Like.user_id == user_id, Like.review_id == review_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def get_by_id(self, like_id: uuid.UUID) -> Like | None:
        stmt = select(Like).where(Like.id == like_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def count_by_review_id(self, review_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Like).where(Like.review_id == review_id)
        result = await self.session.exec(stmt)
        return result.one()

    async def count_user_likes(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(Like.id)).where(Like.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()
