import logging
import uuid
from datetime import UTC, datetime

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.exc import IntegrityError

from src.modules.games.schemas import GameStats
from src.modules.games.service import GameService
from src.modules.review_moderation.models import Judge, ReviewModeration, Verdict
from src.modules.reviews.models import ModerationStatus, Review, ReviewCreate, ReviewUpdate
from src.modules.reviews.repository import ReviewRepository
from src.modules.reviews.schemas import ReviewPagination, ReviewResponse
from src.modules.users.schemas import UserReviewStats
from src.services.moderation_producer.client import ModerationProducer
from src.services.moderation_producer.schemas import ModerationPayload, ModerationType

logger = logging.getLogger("review_service")


class ReviewService:
    def __init__(
        self,
        repo: ReviewRepository,
        game_service: GameService,
        moderation_producer: ModerationProducer,
    ):
        self.repo = repo
        self.game_service = game_service
        self.moderation_producer = moderation_producer

    async def create(
        self, data: ReviewCreate, user_id: uuid.UUID, bg_tasks: BackgroundTasks
    ) -> Review:
        await self.game_service.get_by_id(data.game_id)

        if data.title and not data.content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Content cannot be empty"
            )

        if not data.title and not data.content:
            review = Review(
                **data.model_dump(),
                moderation_status=ModerationStatus.APPROVED,
                moderated_version=1,
            )
        else:
            review = Review(
                **data.model_dump(),
                moderation_status=ModerationStatus.PENDING,
                moderation_enqueued_at=datetime.now(UTC),
            )

        try:
            new_review = await self.repo.create(review, user_id)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You can't have two reviews for the same game.",
            )

        if new_review.title or new_review.content:
            payload = ModerationPayload(
                id=new_review.id,
                version=new_review.content_version,
                type=ModerationType.REVIEW,
                title=new_review.title,
                content=new_review.content,
            )
            bg_tasks.add_task(
                self.moderation_producer.publish,
                routing_key="moderation.review.check",
                payload=payload,
            )
            logger.info(
                "[REVIEWS] Enqueued review %s (v%s) for moderation",
                new_review.id,
                new_review.content_version,
            )
        else:
            logger.info("[REVIEWS] Auto-approved rating-only review %s", new_review.id)
        return new_review

    async def get_by_id_with_likes(
        self, review_id: uuid.UUID, current_user_id: uuid.UUID | None = None
    ) -> ReviewResponse:
        result = await self.repo.get_by_id_with_counters(
            review_id=review_id, current_user_id=current_user_id
        )
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        review, count, is_liked, comments_count = result

        if (
            review.moderation_status == ModerationStatus.REJECTED
            and review.user_id != current_user_id
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        return ReviewResponse.model_validate(
            review,
            update={
                "likes_count": count,
                "liked_by_user": is_liked,
                "comments_count": comments_count,
                "moderation": self._get_moderation_info(review, current_user_id),
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
                "moderation": self._get_moderation_info(review, user_id),
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
                    "moderation": self._get_moderation_info(review, current_user_id),
                },
            )
            for review, count, is_liked, comments_count in result
        ]
        total = await self.repo.count_all(
            user_id=user_id, game_id=game_id, current_user_id=current_user_id
        )
        total_pages = (total - 1 + limit) // limit if total > 0 else 0

        return ReviewPagination(
            items=reviews,
            page=page,
            total=total,
            total_pages=total_pages,
        )

    async def count_all(
        self,
        user_id: uuid.UUID | None = None,
        game_id: uuid.UUID | None = None,
        current_user_id: uuid.UUID | None = None,
    ) -> int:
        total = await self.repo.count_all(user_id, game_id, current_user_id)
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

    async def update(
        self,
        review_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ReviewUpdate,
        bg_tasks: BackgroundTasks,
    ) -> Review:
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        if review.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed")

        updated_fields = data.model_dump(exclude_unset=True)
        new_title = updated_fields.get("title", review.title)
        new_content = updated_fields.get("content", review.content)

        if new_title and not new_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Content cannot be empty if title is provided",
            )

        if new_title != review.title or new_content != review.content:
            review.content_version += 1
            if not new_title and not new_content:
                review.moderation_status = ModerationStatus.APPROVED
                review.moderated_version = review.content_version
                logger.info(
                    "[REVIEWS] Review %s (v%s) cleared text; auto-approved",
                    review.id,
                    review.content_version,
                )
            else:
                review.moderation_enqueued_at = datetime.now(UTC)
                review.moderation_status = (
                    ModerationStatus.PENDING
                    if review.moderation_status != ModerationStatus.REJECTED
                    else ModerationStatus.REJECTED
                )
                payload = ModerationPayload(
                    id=review.id,
                    version=review.content_version,
                    type=ModerationType.REVIEW,
                    title=new_title,
                    content=new_content,
                )
                bg_tasks.add_task(
                    self.moderation_producer.publish,
                    routing_key="moderation.review.check",
                    payload=payload,
                )
                logger.info(
                    "[REVIEWS] Review %s edited to v%s; enqueued for moderation (status=%s)",
                    review.id,
                    review.content_version,
                    review.moderation_status,
                )

        return await self.repo.update(review, data)

    async def appeal(self, review_id: uuid.UUID, user_id: uuid.UUID) -> ReviewResponse:
        review = await self.repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

        if review.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed")

        moderation_info = self._get_moderation_info(review, user_id)
        if not moderation_info or not moderation_info["can_appeal"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This review cannot be appealed.",
            )

        review.moderation_status = ModerationStatus.NEEDS_REVIEW
        appeal_record = ReviewModeration(
            review_id=review.id,
            content_version=review.content_version,
            verdict=Verdict.DOUBT,
            judge=Judge.USER_APPEAL,
            reason=review.moderation_reason,
            scores={},
        )
        await self.repo.save_appeal(review, appeal_record)
        logger.info(
            "[REVIEWS] User %s appealed review %s (v%s)",
            user_id,
            review.id,
            review.content_version,
        )
        return await self.get_by_id_with_likes(review.id, current_user_id=user_id)

    async def update_moderation_info(
        self,
        review: Review,
        moderation_reason: str | None,
        moderation_version: int,
        moderation_status: ModerationStatus,
    ):
        review.moderation_reason = moderation_reason
        review.moderated_version = moderation_version
        review.moderation_status = moderation_status
        await self.repo.update(review, ReviewUpdate())

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

    @staticmethod
    def _get_moderation_info(review: Review, current_user_id: uuid.UUID | None):
        if current_user_id is not None and review.user_id == current_user_id:
            already_appealed_or_decided = any(
                m.content_version == review.content_version
                and m.judge in (Judge.USER_APPEAL, Judge.ADMIN)
                for m in (review.moderations or [])
            )
            can_appeal = (
                review.moderation_status == ModerationStatus.REJECTED
                and review.content_version == review.moderated_version
                and not already_appealed_or_decided
            )
            return {
                "status": review.moderation_status,
                "reason": review.moderation_reason,
                "can_appeal": can_appeal,
            }
        return None
