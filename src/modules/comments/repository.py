import uuid

from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.comments.models import Comment, CommentCreate, CommentUpdate


class CommentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: CommentCreate, user_id: uuid.UUID) -> Comment:
        new_comment = Comment(**data.model_dump(), user_id=user_id)
        self.session.add(new_comment)
        await self.session.flush()
        comment = await self.get_by_id(new_comment.id)
        return comment or new_comment

    async def get_by_id(self, comment_id: uuid.UUID) -> Comment | None:
        stmt = (
            select(Comment)
            .where(Comment.id == comment_id)
            .options(selectinload(Comment.user), selectinload(Comment.review))
        )
        result = await self.session.exec(stmt)
        return result.one()

    async def get_all(self, offset: int, limit: int, review_id: uuid.UUID) -> list[Comment]:
        stmt = (
            select(Comment)
            .where(Comment.review_id == review_id)
            .order_by(Comment.created_at.asc())
            .offset(offset)
            .limit(limit)
            .options(
                selectinload(Comment.user),
                selectinload(Comment.review),
            )
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def update(self, comment: Comment, new_data: CommentUpdate) -> Comment:
        data = new_data.model_dump(exclude_unset=True)
        comment.sqlmodel_update(data)
        self.session.add(comment)
        await self.session.flush()
        await self.session.refresh(comment)
        return comment

    async def delete(self, comment: Comment) -> Comment:
        await self.session.delete(comment)
        await self.session.flush()
        return comment

    async def count_all(self, review_id: uuid.UUID) -> int | None:
        stmt = select(func.count(Comment.id)).where(Comment.review_id == review_id)
        result = await self.session.exec(stmt)
        return result.one()
