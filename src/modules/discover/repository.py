from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlmodel import case, col, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.games.models import Game
from src.modules.reviews.models import Review
from src.modules.users.models import User
from src.modules.wishlists.models import Wishlist
from src.schemas.moderation import ModerationStatus


class DiscoverRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def top_rated_games(self, limit: int = 10) -> Sequence[tuple[Game, float, int]]:
        stmt = (
            select(Game, func.avg(Review.score), func.count(col(Review.id)))
            .join(Review)
            .group_by(col(Game.id))
            .order_by(func.avg(Review.score).desc())
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def top_wanted_games(self, limit: int = 10) -> Sequence[tuple[Game, int]]:
        stmt = (
            select(Game, func.count(col(Wishlist.id)))
            .join(Wishlist)
            .group_by(col(Game.id))
            .order_by(func.count(col(Wishlist.id)).desc())
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def top_reviewed_games(self, limit: int = 10) -> Sequence[tuple[Game, int, int]]:
        last_week = self._get_last_week_date()
        new_reviews_count = case((Review.created_at >= last_week, 1), else_=0)
        stmt = (
            select(Game, func.count(col(Review.id)), func.sum(new_reviews_count))
            .join(Review)
            .group_by(col(Game.id))
            .order_by(func.count(col(Review.id)).desc())
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def user_with_the_most_reviews(self, limit: int = 10) -> Sequence[tuple[User, int, int]]:
        last_week = self._get_last_week_date()
        new_reviews_count = case((Review.created_at >= last_week, 1), else_=0)
        stmt = (
            select(User, func.count(col(Review.id)), func.sum(new_reviews_count))
            .join(Review)
            .group_by(col(User.id))
            .order_by(func.count(col(Review.id)).desc())
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def reviews_amount(self) -> tuple[int, int]:
        last_week = self._get_last_week_date()
        new_reviews_count = case((Review.created_at >= last_week, 1), else_=0)
        stmt = select(
            func.count(col(Review.id)).label("reviews_count"),
            func.sum(new_reviews_count).label("new_reviews_count"),
        ).where(
            Review.moderation_status != ModerationStatus.REJECTED,
            or_(col(Review.title).is_not(None), col(Review.content).is_not(None)),
        )
        result = await self.session.exec(stmt)
        counts = result.one()
        return counts.reviews_count, counts.new_reviews_count

    @staticmethod
    def _get_last_week_date() -> datetime:
        return datetime.now(UTC) - timedelta(days=7)
