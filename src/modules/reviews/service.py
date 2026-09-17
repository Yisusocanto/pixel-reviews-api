import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.modules.games.service import GameService
from src.modules.reviews.models import Review, ReviewCreate
from src.modules.reviews.repository import ReviewRepository
from src.modules.reviews.schemas import ReviewPagination


class ReviewService:
    def __init__(self, repo: ReviewRepository, game_service: GameService):
        self.repo = repo
        self.game_service = game_service

    async def create(self, data: ReviewCreate, user_id: uuid.UUID) -> Review:
        await self.game_service.get_by_id(data.game_id)
        try:
            new_review = await self.repo.create(data, user_id)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You can't have two reviews for the same game.",
            )

        return new_review

    async def get_by_id(self, review_id: uuid.UUID) -> Review | None:
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        return review

    async def get_all(
        self,
        page: int,
        limit: int,
        user_id: uuid.UUID | None = None,
        game_id: uuid.UUID | None = None,
    ) -> ReviewPagination:
        offset = (page - 1) * limit
        reviews = await self.repo.get_all(offset, limit, user_id, game_id)
        total = await self.repo.count_all(user_id=user_id, game_id=game_id)
        total_pages = (total - 1 + limit) // limit if total > 0 else 0

        return ReviewPagination(
            items=reviews,
            page=page,
            total=total,
            total_pages=total_pages,
        )

    async def count_all(
        self, user_id: uuid.UUID | None = None, game_id: uuid.UUID | None = None
    ) -> int:
        total = await self.repo.count_all(user_id, game_id)
        return total
