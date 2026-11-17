import uuid

from sqlalchemy.orm import selectinload
from sqlmodel import func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.review_moderation.models import ReviewModeration
from src.modules.reviews.models import ModerationStatus, Review


class ReviewModerationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: ReviewModeration) -> ReviewModeration:
        self.session.add(data)
        await self.session.flush()
        await self.session.refresh(data)
        return data

    async def save_verdict(self, review: Review, moderation: ReviewModeration) -> Review:
        self.session.add(review)
        self.session.add(moderation)
        await self.session.commit()
        return await self.get_review_with_relations(review.id) or review

    async def get_review_with_relations(self, review_id: uuid.UUID) -> Review | None:
        stmt = (
            select(Review)
            .where(Review.id == review_id)
            .options(
                selectinload(Review.user),
                selectinload(Review.game),
                selectinload(Review.moderations).selectinload(ReviewModeration.admin),
            )
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_history_by_review_id(self, review_id: uuid.UUID) -> list[ReviewModeration]:
        stmt = (
            select(ReviewModeration)
            .where(ReviewModeration.review_id == review_id)
            .options(selectinload(ReviewModeration.admin))
            .order_by(ReviewModeration.created_at.desc())
        )
        result = await self.session.exec(stmt)
        return list(result.all())

    async def get_moderation_queue(
        self,
        status_filter: ModerationStatus | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Review], int]:
        base_condition = or_(Review.title.is_not(None), Review.content.is_not(None))

        stmt = (
            select(Review)
            .where(base_condition)
            .options(
                selectinload(Review.user),
                selectinload(Review.game),
                selectinload(Review.moderations).selectinload(ReviewModeration.admin),
            )
            .order_by(Review.updated_at.desc(), Review.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_stmt = select(func.count(Review.id)).where(base_condition)

        if status_filter is not None:
            stmt = stmt.where(Review.moderation_status == status_filter)
            count_stmt = count_stmt.where(Review.moderation_status == status_filter)

        items_res = await self.session.exec(stmt)
        total_res = await self.session.exec(count_stmt)
        total = total_res.first() or 0

        return list(items_res.all()), total
