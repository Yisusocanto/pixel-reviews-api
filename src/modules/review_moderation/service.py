import uuid

from fastapi import HTTPException, status

from src.modules.review_moderation.models import Judge, ReviewModeration, Verdict
from src.modules.review_moderation.repository import ReviewModerationRepository
from src.modules.review_moderation.schemas import (
    AdminDecisionRequest,
    AdminModerationQueuePagination,
    AdminModerationReviewItem,
    ModerationVerdictRequest,
    ModerationVerdictResult,
    ReviewModerationHistoryItem,
)
from src.modules.reviews.models import ModerationStatus, Review
from src.modules.reviews.service import ReviewService
from src.modules.users.models import User

rules = {
    Verdict.REJECT: ModerationStatus.REJECTED,
    Verdict.APPROVE: ModerationStatus.APPROVED,
    Verdict.DOUBT: ModerationStatus.NEEDS_REVIEW,
}


class ReviewModerationService:
    def __init__(self, repo: ReviewModerationRepository, review_service: ReviewService):
        self.repo = repo
        self.review_service = review_service

    async def create(self, data: ModerationVerdictRequest) -> ModerationVerdictResult:
        review = await self.review_service.get_by_id(data.id)
        if data.version != review.content_version:
            return ModerationVerdictResult(result="stale")

        if data.version == review.moderated_version:
            return ModerationVerdictResult(result="duplicate")

        review.moderation_reason = data.reason if data.verdict != Verdict.APPROVE else None
        review.moderated_version = data.version
        review.moderation_status = rules.get(data.verdict, ModerationStatus.NEEDS_REVIEW)

        moderation = ReviewModeration(
            review_id=data.id,
            content_version=data.version,
            verdict=data.verdict,
            judge=data.judge,
            reason=data.reason,
            scores=data.scores,
        )
        await self.repo.save_verdict(review, moderation)
        return ModerationVerdictResult(result="applied")

    async def get_queue(
        self,
        status_filter: ModerationStatus | None,
        page: int,
        limit: int,
    ) -> AdminModerationQueuePagination:
        offset = (page - 1) * limit
        reviews, total = await self.repo.get_moderation_queue(
            status_filter=status_filter,
            offset=offset,
            limit=limit,
        )
        items = [self._to_admin_review_item(r) for r in reviews]
        total_pages = (total - 1 + limit) // limit if total > 0 else 0
        return AdminModerationQueuePagination(
            items=items,
            page=page,
            total=total,
            total_pages=total_pages,
        )

    async def get_history(self, review_id: uuid.UUID) -> list[ReviewModerationHistoryItem]:
        await self.review_service.get_by_id(review_id)
        records = await self.repo.get_history_by_review_id(review_id)
        return [ReviewModerationHistoryItem.model_validate(r) for r in records]

    async def decide(
        self,
        review_id: uuid.UUID,
        data: AdminDecisionRequest,
        admin_user: User,
    ) -> AdminModerationReviewItem:
        review = await self.review_service.get_by_id(review_id)
        if data.version != review.content_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Review content was modified by the author. Please reload.",
            )

        if data.decision == "approve":
            verdict = Verdict.APPROVE
            new_status = ModerationStatus.APPROVED
            reason = None
        else:
            verdict = Verdict.REJECT
            new_status = ModerationStatus.REJECTED
            reason = data.reason or review.moderation_reason or "policy_violation"

        review.moderation_status = new_status
        review.moderation_reason = reason
        review.moderated_version = review.content_version

        moderation = ReviewModeration(
            review_id=review.id,
            content_version=review.content_version,
            verdict=verdict,
            judge=Judge.ADMIN,
            reason=reason,
            scores={},
            admin_id=admin_user.id,
            note=data.note,
        )
        updated_review = await self.repo.save_verdict(review, moderation)
        return self._to_admin_review_item(updated_review)

    @staticmethod
    def _to_admin_review_item(review: Review) -> AdminModerationReviewItem:
        sorted_mods = sorted(
            review.moderations or [],
            key=lambda m: m.created_at,
            reverse=True,
        )
        latest = ReviewModerationHistoryItem.model_validate(sorted_mods[0]) if sorted_mods else None
        is_appeal = any(
            m.content_version == review.content_version and m.judge == Judge.USER_APPEAL
            for m in sorted_mods
        )
        return AdminModerationReviewItem.model_validate(
            review,
            update={
                "latest_moderation": latest,
                "is_appeal": is_appeal,
            },
        )
