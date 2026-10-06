import uuid

from sqlalchemy import exists, literal
from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.comments.models import Comment
from src.modules.likes.models import Like
from src.modules.reviews.models import Review, ReviewCreate, ReviewUpdate


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

    async def get_by_id_with_counters(
        self, review_id: uuid.UUID, current_user_id: uuid.UUID | None = None
    ) -> tuple[Review, int, bool, int] | None:
        likes_count = self._get_likes_count()
        liked_by_user = self._get_liked_by_user(current_user_id)
        comments_count = self._get_comments_count()
        stmt = (
            select(Review, likes_count, liked_by_user, comments_count)
            .where(Review.id == review_id)
            .options(selectinload(Review.user), selectinload(Review.game))
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_user_game_review(
        self, game_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[Review, int, bool, int] | None:
        likes_count = self._get_likes_count()
        liked_by_user = self._get_liked_by_user(user_id)
        comments_count = self._get_comments_count()

        stmt = (
            select(Review, likes_count, liked_by_user, comments_count)
            .where(Review.game_id == game_id, Review.user_id == user_id)
            .options(
                selectinload(Review.game),
                selectinload(Review.user),
            )
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_all(
        self,
        offset: int,
        limit: int,
        user_id: uuid.UUID | None = None,
        game_id: uuid.UUID | None = None,
        current_user_id: uuid.UUID | None = None,
    ) -> list[tuple[Review, int, bool, int]]:
        likes_count = self._get_likes_count()
        liked_by_user = self._get_liked_by_user(current_user_id)
        comments_count = self._get_comments_count()
        stmt = (
            select(Review, likes_count, liked_by_user, comments_count)
            .where(Review.title != None)
            .order_by(Review.created_at.desc())
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
        """Returns only the number of reviews that have a title and content"""
        stmt = select(func.count(Review.id)).where(Review.title != None)
        if user_id:
            stmt = stmt.where(Review.user_id == user_id)

        if game_id:
            stmt = stmt.where(Review.game_id == game_id)

        result = await self.session.exec(stmt)
        total = result.first()
        return total if total is not None else 0

    async def count_all_ratings(
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

    async def delete(self, review: Review) -> Review:
        await self.session.delete(review)
        await self.session.flush()
        return review

    async def update(self, review: Review, new_data: ReviewUpdate) -> Review:
        data = new_data.model_dump(exclude_unset=True)
        review.sqlmodel_update(data)
        self.session.add(review)
        await self.session.flush()
        updated_review = await self.get_by_id(review.id)
        return updated_review or review

    async def get_avg_rating(self, game_id: uuid.UUID) -> float | None:
        stmt = select(func.avg(Review.score)).where(Review.game_id == game_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def get_user_avg_rating(self, user_id: uuid.UUID) -> float | None:
        stmt = select(func.avg(Review.score)).where(Review.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.first()

    async def get_score_distribution(self, game_id: uuid.UUID):
        stmt = (
            select(Review.score, func.count(Review.score))
            .where(Review.game_id == game_id)
            .group_by(Review.score)
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def get_user_score_distribution(self, user_id: uuid.UUID):
        stmt = (
            select(Review.score, func.count(Review.score))
            .where(Review.user_id == user_id)
            .group_by(Review.score)
        )
        result = await self.session.exec(stmt)
        return result.all()

    def _get_likes_count(self):
        likes_count = (
            select(func.count())
            .select_from(Like)
            .where(Like.review_id == Review.id)
            .scalar_subquery()
            .label("likes_count")
        )
        return likes_count

    def _get_liked_by_user(self, current_user_id: uuid.UUID | None):
        if not current_user_id:
            return literal(False).label("liked_by_user")
        liked_by_user = (
            exists()
            .where(Like.review_id == Review.id, Like.user_id == current_user_id)
            .label("liked_by_user")
        )
        return liked_by_user

    def _get_comments_count(self):
        comments_count = (
            select(func.count())
            .select_from(Comment)
            .where(Comment.review_id == Review.id)
            .scalar_subquery()
            .label("comments_count")
        )
        return comments_count
