from fastapi import APIRouter, Depends

from src.modules.review_moderation.dependencies import (
    ReviewModerationServiceDep,
    verify_service_key,
)
from src.modules.review_moderation.schemas import ModerationVerdictRequest, ModerationVerdictResult

router = APIRouter(
    prefix="/internal/moderation",
    tags=["Review Moderation"],
    dependencies=[Depends(verify_service_key)],
)


@router.post("/verdicts", response_model=ModerationVerdictResult)
async def create(service: ReviewModerationServiceDep, data: ModerationVerdictRequest):
    """
    Endpoint to create a moderation verdict for a review.
    """
    return await service.create(data)
