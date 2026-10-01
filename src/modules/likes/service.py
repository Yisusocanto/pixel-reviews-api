import uuid

from fastapi import HTTPException, status

from src.modules.likes.repository import LikeRepository
from src.modules.reviews.repository import ReviewRepository


class LikeService:
    def __init__(self, repo: LikeRepository, review_repo: ReviewRepository):
        self.repo = repo
        self.review_repo = review_repo

    async def toggle(self, review_id: uuid.UUID, user_id: uuid.UUID) -> tuple[bool, int]:
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        existing_like = await self.repo.get_user_review_like(user_id=user_id, review_id=review_id)
        if not existing_like:
            await self.repo.create(review_id=review_id, user_id=user_id)
            liked = True
        else:
            await self.repo.remove(existing_like)
            liked = False

        likes_count = await self.repo.count_by_review_id(review_id)
        return liked, likes_count
