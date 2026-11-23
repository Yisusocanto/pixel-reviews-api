import uuid

from sqlalchemy.orm import selectinload
from sqlmodel import col, func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.comment_moderation.models import CommentModeration
from src.modules.comments.models import Comment, CommentUpdate
from src.schemas.moderation import ModerationStatus


class CommentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, comment: Comment, user_id: uuid.UUID) -> Comment:
        comment.user_id = user_id
        self.session.add(comment)
        await self.session.commit()
        created_comment = await self.get_by_id(comment.id)
        return created_comment or comment

    async def get_by_id(self, comment_id: uuid.UUID) -> Comment | None:
        stmt = (
            select(Comment)
            .where(Comment.id == comment_id)
            .options(
                selectinload(Comment.user),
                selectinload(Comment.review),
                selectinload(Comment.moderations),
            )
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_all(
        self,
        offset: int,
        limit: int,
        review_id: uuid.UUID,
        current_user_id: uuid.UUID | None = None,
    ) -> list[Comment]:
        stmt = (
            select(Comment)
            .where(
                Comment.review_id == review_id,
                self._visibility_filter(current_user_id),
            )
            .order_by(col(Comment.created_at).asc())
            .offset(offset)
            .limit(limit)
            .options(
                selectinload(Comment.user),
                selectinload(Comment.review),
                selectinload(Comment.moderations),
            )
        )
        result = await self.session.exec(stmt)
        return list(result.all())

    async def update(self, comment: Comment, new_data: CommentUpdate) -> Comment:
        data = new_data.model_dump(exclude_unset=True)
        comment.sqlmodel_update(data)
        self.session.add(comment)
        await self.session.commit()
        updated_comment = await self.get_by_id(comment.id)
        return updated_comment or comment

    async def save_appeal(self, comment: Comment, moderation: CommentModeration) -> Comment:
        self.session.add(comment)
        self.session.add(moderation)
        await self.session.commit()
        updated_comment = await self.get_by_id(comment.id)
        return updated_comment or comment

    async def delete(self, comment: Comment) -> Comment:
        await self.session.delete(comment)
        await self.session.flush()
        return comment

    async def count_all(
        self,
        review_id: uuid.UUID,
        current_user_id: uuid.UUID | None = None,
    ) -> int:
        stmt = select(func.count(Comment.id)).where(
            Comment.review_id == review_id,
            self._visibility_filter(current_user_id),
        )
        result = await self.session.exec(stmt)
        total = result.first()
        return total if total is not None else 0

    @staticmethod
    def _visibility_filter(current_user_id: uuid.UUID | None):
        if current_user_id is not None:
            return or_(
                Comment.moderation_status != ModerationStatus.REJECTED,
                Comment.user_id == current_user_id,
            )
        return Comment.moderation_status != ModerationStatus.REJECTED
