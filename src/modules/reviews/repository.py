import uuid

from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.reviews.models import Review, ReviewCreate


class ReviewRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: ReviewCreate, user_id: uuid.UUID) -> Review:
        new_review = Review(**data.model_dump(), user_id=user_id)
        self.session.add(new_review)
        await self.session.flush()
        created_review = await self.get_by_id(new_review.id)
        return created_review or new_review

    async def get_by_id(self, review_id: uuid.UUID) -> Review | None:
        stmt = (
            select(Review)
            .where(Review.id == review_id)
            .options(selectinload(Review.user), selectinload(Review.game))
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_all(
        self,
        offset: int,
        limit: int,
        user_id: uuid.UUID | None = None,
        game_id: uuid.UUID | None = None,
    ) -> list[Review]:
        stmt = (
            select(Review)
            .offset(offset)
            .limit(limit)
            .options(selectinload(Review.user), selectinload(Review.game))
        )
        if user_id:
            stmt = stmt.where(Review.user_id == user_id)

        if game_id:
            stmt = stmt.where(Review.game_id == game_id)

        result = await self.session.exec(stmt)
        return result.all()

    async def count_all(
        self, user_id: uuid.UUID | None = None, game_id: uuid.UUID | None = None
    ) -> int:
        stmt = select(func.count(Review.id))
        if user_id:
            stmt = stmt.where(Review.user_id == user_id)

        if game_id:
            stmt = stmt.where(Review.game_id == game_id)

        result = await self.session.exec(stmt)
        total = result.first()
        return total if total is not None else 0
