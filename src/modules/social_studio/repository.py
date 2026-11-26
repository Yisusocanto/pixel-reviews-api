import uuid
from collections.abc import Sequence

from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.games.models import Game
from src.modules.likes.models import Like
from src.modules.reviews.models import Review
from src.modules.wishlists.models import Wishlist
from src.schemas.moderation import ModerationStatus


class SocialStudioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_games_with_community_stats(
        self, limit: int = 20
    ) -> Sequence[tuple[Game, float | None, int]]:
        stmt = (
            select(
                Game,
                func.avg(Review.score).label("avg_score"),
                func.count(col(Review.id)).label("reviews_count"),
            )
            .outerjoin(Review, Review.game_id == Game.id)
            .options(
                selectinload(Game.genres),
                selectinload(Game.developers),
                selectinload(Game.platforms),
            )
            .group_by(col(Game.id))
            .order_by(func.count(col(Review.id)).desc(), col(Game.critic_score).desc().nullslast())
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def get_hidden_gem_games(
        self, limit: int = 12
    ) -> Sequence[tuple[Game, float | None, int]]:
        stmt = (
            select(
                Game,
                func.avg(Review.score).label("avg_score"),
                func.count(col(Review.id)).label("reviews_count"),
            )
            .outerjoin(Review, Review.game_id == Game.id)
            .where(col(Game.critic_score).is_not(None), col(Game.critic_score) >= 78)
            .options(
                selectinload(Game.genres),
                selectinload(Game.developers),
                selectinload(Game.platforms),
            )
            .group_by(col(Game.id))
            .order_by(func.count(col(Review.id)).asc(), col(Game.critic_score).desc())
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        rows = result.all()
        if rows:
            return rows
        return await self.get_games_with_community_stats(limit=limit)

    async def get_most_anticipated_games(self, limit: int = 12) -> Sequence[tuple[Game, int]]:
        stmt = (
            select(Game, func.count(col(Wishlist.id)).label("wish_count"))
            .outerjoin(Wishlist, Wishlist.game_id == Game.id)
            .options(
                selectinload(Game.genres),
                selectinload(Game.developers),
                selectinload(Game.platforms),
            )
            .group_by(col(Game.id))
            .order_by(
                func.count(col(Wishlist.id)).desc(), col(Game.release_date).desc().nullslast()
            )
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def get_featured_reviews(self, limit: int = 15) -> Sequence[tuple[Review, int]]:
        likes_count = (
            select(func.count())
            .select_from(Like)
            .where(Like.review_id == Review.id)
            .scalar_subquery()
            .label("likes_count")
        )
        stmt = (
            select(Review, likes_count)
            .where(
                col(Review.title).is_not(None),
                col(Review.content).is_not(None),
                Review.moderation_status != ModerationStatus.REJECTED,
            )
            .options(
                selectinload(Review.user),
                selectinload(Review.game).selectinload(Game.genres),
                selectinload(Review.game).selectinload(Game.developers),
                selectinload(Review.game).selectinload(Game.platforms),
            )
            .order_by(likes_count.desc(), col(Review.created_at).desc())
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def get_game_by_slug_with_stats(self, slug: str) -> tuple[Game, float | None, int] | None:
        stmt = (
            select(
                Game,
                func.avg(Review.score).label("avg_score"),
                func.count(col(Review.id)).label("reviews_count"),
            )
            .outerjoin(Review, Review.game_id == Game.id)
            .where(Game.slug == slug)
            .options(
                selectinload(Game.genres),
                selectinload(Game.developers),
                selectinload(Game.platforms),
            )
            .group_by(col(Game.id))
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_review_by_id(self, review_id: uuid.UUID) -> Review | None:
        stmt = (
            select(Review)
            .where(Review.id == review_id)
            .options(
                selectinload(Review.user),
                selectinload(Review.game).selectinload(Game.genres),
                selectinload(Review.game).selectinload(Game.developers),
                selectinload(Review.game).selectinload(Game.platforms),
            )
        )
        result = await self.session.exec(stmt)
        return result.first()
