import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.modules.games.schemas import GameStats
from src.modules.games.service import GameService
from src.modules.reviews.models import Review, ReviewCreate, ReviewUpdate
from src.modules.reviews.repository import ReviewRepository
from src.modules.reviews.schemas import ReviewPagination, ReviewResponse
from src.modules.users.schemas import UserReviewStats


class ReviewService:
    def __init__(self, repo: ReviewRepository, game_service: GameService):
        self.repo = repo
        self.game_service = game_service

    async def create(self, data: ReviewCreate, user_id: uuid.UUID) -> Review:
        await self.game_service.get_by_id(data.game_id)

        if data.title and not data.content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Content cannot be empty"
            )

        try:
            new_review = await self.repo.create(data, user_id)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You can't have two reviews for the same game.",
            )

        return new_review

    async def get_by_id_with_likes(
        self, review_id: uuid.UUID, current_user_id: uuid.UUID | None = None
    ) -> ReviewResponse:
        result = await self.repo.get_by_id_with_counters(review_id, current_user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        review, count, is_liked, comments_count = result
        return ReviewResponse.model_validate(
            review,
            update={
                "likes_count": count,
                "liked_by_user": is_liked,
                "comments_count": comments_count,
            },
        )

    async def get_by_id(self, review_id: uuid.UUID) -> Review:
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        return review

    async def get_user_game_review(self, game_id: uuid.UUID, user_id: uuid.UUID) -> ReviewResponse:
        game = await self.game_service.get_by_id(game_id)
        result = await self.repo.get_user_game_review(game.id, user_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        review, count, is_liked, comments_count = result
        return ReviewResponse.model_validate(
            review,
            update={
                "likes_count": count,
                "liked_by_user": is_liked,
                "comments_count": comments_count,
            },
        )

    async def get_all(
        self,
        page: int,
        limit: int,
        user_id: uuid.UUID | None = None,
        game_id: uuid.UUID | None = None,
        current_user_id: uuid.UUID | None = None,
    ) -> ReviewPagination:
        offset = (page - 1) * limit
        result = await self.repo.get_all(
            offset=offset,
            limit=limit,
            user_id=user_id,
            game_id=game_id,
            current_user_id=current_user_id,
        )
        reviews = [
            ReviewResponse.model_validate(
                review,
                update={
                    "likes_count": count,
                    "liked_by_user": is_liked,
                    "comments_count": comments_count,
                },
            )
            for review, count, is_liked, comments_count in result
        ]
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

    async def delete(self, review_id: uuid.UUID, user_id: uuid.UUID) -> Review:
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found",
            )

        if review.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed")

        return await self.repo.delete(review)

    async def update(self, review_id: uuid.UUID, user_id: uuid.UUID, data: ReviewUpdate) -> Review:
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        if review.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed")

        return await self.repo.update(review, data)

    async def game_stats(self, game_id: uuid.UUID):
        total = await self.repo.count_all_ratings(game_id=game_id)
        avg_rating = await self.repo.get_avg_rating(game_id)
        distribution = await self.repo.get_score_distribution(game_id)
        distribution_dict = dict(distribution)
        rating_distribution = [
            {
                "stars": score,
                "percentage": (distribution_dict.get(score, 1) / total) * 100
                if distribution_dict.get(score, 0) != 0
                else 0,
                "count": distribution_dict.get(score, 0),
            }
            for score in range(1, 6)
        ]
        return GameStats(
            total_reviews=total,
            avg_ratings=avg_rating if avg_rating is not None else 0,
            rating_distribution=rating_distribution,
        )

    async def user_stats(self, user_id: uuid.UUID):
        total_ratings = await self.repo.count_all_ratings(user_id=user_id)
        total_reviews = await self.repo.count_all(user_id=user_id)
        avg_ratings = await self.repo.get_user_avg_rating(user_id=user_id)
        distribution = await self.repo.get_user_score_distribution(user_id=user_id)
        distribution_dict = dict(distribution)
        rating_distribution = [
            {
                "stars": score,
                "percentage": (distribution_dict.get(score, 1) / total_ratings) * 100
                if distribution_dict.get(score, 0) != 0
                else 0,
                "count": distribution_dict.get(score, 0),
            }
            for score in range(1, 6)
        ]
        return UserReviewStats(
            total_reviews=total_reviews,
            total_ratings=total_ratings,
            avg_rating=avg_ratings if avg_ratings is not None else 0,
            rating_distribution=rating_distribution,
        )
