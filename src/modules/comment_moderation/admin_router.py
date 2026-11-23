import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.modules.auth.dependencies import AdminDep, require_admin
from src.modules.comment_moderation.dependencies import CommentModerationServiceDep
from src.modules.comment_moderation.schemas import (
    AdminModerationCommentItem,
    AdminModerationCommentQueuePagination,
    CommentModerationHistoryItem,
)
from src.schemas.moderation import AdminDecisionRequest, ModerationStatus

router = APIRouter(
    prefix="/admin/moderation",
    tags=["Admin Moderation"],
    dependencies=[Depends(require_admin)],
)


@router.get("/comments", response_model=AdminModerationCommentQueuePagination)
async def get_moderation_comments(
    service: CommentModerationServiceDep,
    status: Annotated[ModerationStatus | None, Query()] = ModerationStatus.NEEDS_REVIEW,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return await service.get_queue(status_filter=status, page=page, limit=limit)


@router.get("/comments/{comment_id}/history", response_model=list[CommentModerationHistoryItem])
async def get_comment_moderation_history(
    comment_id: uuid.UUID,
    service: CommentModerationServiceDep,
):
    return await service.get_history(comment_id=comment_id)


@router.post("/comments/{comment_id}/decision", response_model=AdminModerationCommentItem)
async def decide_comment_moderation(
    comment_id: uuid.UUID,
    data: AdminDecisionRequest,
    service: CommentModerationServiceDep,
    admin_user: AdminDep,
):
    return await service.decide(comment_id=comment_id, data=data, admin_user=admin_user)
