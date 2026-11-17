from src.modules.review_moderation.models import ReviewModeration, Verdict
from src.modules.review_moderation.repository import ReviewModerationRepository
from src.modules.review_moderation.schemas import ModerationVerdictRequest, ModerationVerdictResult
from src.modules.reviews.models import ModerationStatus
from src.modules.reviews.service import ReviewService

rules = {
    Verdict.REJECT: ModerationStatus.REJECTED,
    Verdict.APPROVE: ModerationStatus.APPROVED,
    Verdict.DOUBT: ModerationStatus.NEEDS_REVIEW,
}


class ReviewModerationService:
    def __init__(self, repo: ReviewModerationRepository, review_service: ReviewService):
        self.repo = repo
        self.review_service = review_service

    async def create(self, data: ModerationVerdictRequest):
        review = await self.review_service.get_by_id(data.id)
        if data.version != review.content_version:
            return ModerationVerdictResult(result="stale")

        if data.version == review.moderated_version:
            return ModerationVerdictResult(result="duplicate")

        await self.review_service.update_moderation_info(
            review,
            moderation_reason=data.reason,
            moderation_version=data.version,
            moderation_status=rules.get(data.verdict, ModerationStatus.NEEDS_REVIEW),
        )
        await self.repo.create(
            ReviewModeration(
                review_id=data.id,
                content_version=data.version,
                verdict=data.verdict,
                judge=data.judge,
                reason=data.reason,
                scores=data.scores,
            )
        )
        return ModerationVerdictResult(result="applied")
