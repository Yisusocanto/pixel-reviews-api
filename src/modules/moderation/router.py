from fastapi import APIRouter, Depends

from src.modules.comment_moderation.dependencies import CommentModerationServiceDep
from src.modules.moderation.dependencies import verify_service_key
from src.modules.review_moderation.dependencies import ReviewModerationServiceDep
from src.schemas.moderation import ModerationVerdictRequest, ModerationVerdictResult
from src.services.moderation_producer.schemas import ModerationType

router = APIRouter(
    prefix="/internal/moderation",
    tags=["Internal Moderation"],
    dependencies=[Depends(verify_service_key)],
)


@router.post("/verdicts", response_model=ModerationVerdictResult)
async def moderation_verdict(
    review_moderation_service: ReviewModerationServiceDep,
    comment_moderation_service: CommentModerationServiceDep,
    data: ModerationVerdictRequest,
) -> ModerationVerdictResult:
    match data.type:
        case ModerationType.REVIEW:
            return await review_moderation_service.create(data)
        case ModerationType.COMMENT:
            return await comment_moderation_service.create(data)
