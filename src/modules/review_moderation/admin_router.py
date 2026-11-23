import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.modules.auth.dependencies import AdminDep, require_admin
from src.modules.review_moderation.dependencies import ReviewModerationServiceDep
from src.modules.review_moderation.schemas import (
    AdminModerationQueuePagination,
    AdminModerationReviewItem,
    ReviewModerationHistoryItem,
)
from src.schemas.moderation import AdminDecisionRequest, ModerationStatus

router = APIRouter(
    prefix="/admin/moderation",
    tags=["Admin Moderation"],
    dependencies=[Depends(require_admin)],
)


@router.get("/reviews", response_model=AdminModerationQueuePagination)
async def get_moderation_reviews(
    service: ReviewModerationServiceDep,
    status: Annotated[ModerationStatus | None, Query()] = ModerationStatus.NEEDS_REVIEW,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return await service.get_queue(status_filter=status, page=page, limit=limit)


@router.get("/reviews/{review_id}/history", response_model=list[ReviewModerationHistoryItem])
async def get_review_moderation_history(
    review_id: uuid.UUID,
    service: ReviewModerationServiceDep,
):
    return await service.get_history(review_id=review_id)


@router.post("/reviews/{review_id}/decision", response_model=AdminModerationReviewItem)
async def decide_review_moderation(
    review_id: uuid.UUID,
    data: AdminDecisionRequest,
    service: ReviewModerationServiceDep,
    admin_user: AdminDep,
):
    return await service.decide(review_id=review_id, data=data, admin_user=admin_user)
