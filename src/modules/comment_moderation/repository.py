import uuid

from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.comment_moderation.models import CommentModeration
from src.modules.comments.models import Comment
from src.modules.reviews.models import Review
from src.schemas.moderation import ModerationStatus


class CommentModerationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: CommentModeration) -> CommentModeration:
        self.session.add(data)
        await self.session.flush()
        await self.session.refresh(data)
        return data

    async def save_verdict(self, comment: Comment, moderation: CommentModeration) -> Comment:
        self.session.add(comment)
        self.session.add(moderation)
        await self.session.commit()
        return await self.get_comment_with_relations(comment.id) or comment

    async def get_comment_with_relations(self, comment_id: uuid.UUID) -> Comment | None:
        stmt = (
            select(Comment)
            .where(Comment.id == comment_id)
            .options(
                selectinload(Comment.user),
                selectinload(Comment.review).selectinload(Review.game),
                selectinload(Comment.review).selectinload(Review.user),
                selectinload(Comment.moderations).selectinload(CommentModeration.admin),
            )
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_history_by_comment_id(self, comment_id: uuid.UUID) -> list[CommentModeration]:
        stmt = (
            select(CommentModeration)
            .where(CommentModeration.comment_id == comment_id)
            .options(selectinload(CommentModeration.admin))
            .order_by(CommentModeration.created_at.desc())
        )
        result = await self.session.exec(stmt)
        return list(result.all())

    async def get_moderation_queue(
        self,
        status_filter: ModerationStatus | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Comment], int]:
        stmt = (
            select(Comment)
            .options(
                selectinload(Comment.user),
                selectinload(Comment.review).selectinload(Review.game),
                selectinload(Comment.review).selectinload(Review.user),
                selectinload(Comment.moderations).selectinload(CommentModeration.admin),
            )
            .order_by(Comment.updated_at.desc(), Comment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        count_stmt = select(func.count(Comment.id))

        if status_filter is not None:
            stmt = stmt.where(Comment.moderation_status == status_filter)
            count_stmt = count_stmt.where(Comment.moderation_status == status_filter)

        items_res = await self.session.exec(stmt)
        total_res = await self.session.exec(count_stmt)
        total = total_res.first() or 0

        return list(items_res.all()), total
