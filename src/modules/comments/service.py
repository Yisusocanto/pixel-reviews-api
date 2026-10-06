import uuid

from fastapi import HTTPException, status

from src.modules.comments.models import Comment, CommentCreate, CommentUpdate
from src.modules.comments.repository import CommentRepository
from src.modules.comments.schemas import CommentPagination
from src.modules.reviews.service import ReviewService


class CommentService:
    def __init__(self, repo: CommentRepository, review_service: ReviewService):
        self.repo = repo
        self.review_service = review_service

    async def create(self, data: CommentCreate, user_id: uuid.UUID) -> Comment:
        await self.review_service.get_by_id(data.review_id)

        new_comment = await self.repo.create(data, user_id)
        return new_comment

    async def get_by_id(self, comment_id: uuid.UUID) -> Comment:
        comment = await self.repo.get_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        return comment

    async def get_all(self, page: int, limit: int, review_id: uuid.UUID) -> CommentPagination:
        offset = (page - 1) * limit
        comments = await self.repo.get_all(offset=offset, limit=limit, review_id=review_id)
        total = await self.repo.count_all(review_id=review_id)
        total_pages = (page - 1 + limit) // limit if total > 0 else 0

        return CommentPagination(
            items=comments,
            total=total if total else 0,
            total_pages=total_pages,
            page=page,
        )

    async def update(
        self, comment_id: uuid.UUID, user_id: uuid.UUID, new_data: CommentUpdate
    ) -> Comment:
        comment = await self.get_by_id(comment_id)
        if comment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed")

        updated_comment = await self.repo.update(comment, new_data)
        return updated_comment

    async def delete(self, comment_id: uuid.UUID, user_id: uuid.UUID) -> Comment:
        comment = await self.get_by_id(comment_id)
        if comment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed")

        return await self.repo.delete(comment)
