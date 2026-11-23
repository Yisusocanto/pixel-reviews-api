import uuid

from fastapi import HTTPException, status

from src.modules.comment_moderation.models import CommentModeration
from src.modules.comment_moderation.repository import CommentModerationRepository
from src.modules.comment_moderation.schemas import (
    AdminModerationCommentItem,
    AdminModerationCommentQueuePagination,
    CommentModerationHistoryItem,
)
from src.modules.comments.models import Comment
from src.modules.comments.service import CommentService
from src.modules.users.models import User
from src.schemas.moderation import (
    VERDICT_STATUS_MAP,
    AdminDecisionRequest,
    Judge,
    ModerationStatus,
    ModerationVerdictRequest,
    ModerationVerdictResult,
    Verdict,
)


class CommentModerationService:
    def __init__(self, repo: CommentModerationRepository, comment_service: CommentService):
        self.repo = repo
        self.comment_service = comment_service

    async def create(self, data: ModerationVerdictRequest) -> ModerationVerdictResult:
        comment = await self.comment_service.get_by_id(data.id)
        if data.version != comment.content_version:
            return ModerationVerdictResult(result="stale")

        if data.version == comment.moderated_version:
            return ModerationVerdictResult(result="duplicate")

        comment.moderation_reason = data.reason if data.verdict != Verdict.APPROVE else None
        comment.moderated_version = data.version
        comment.moderation_status = VERDICT_STATUS_MAP.get(
            data.verdict, ModerationStatus.NEEDS_REVIEW
        )

        moderation = CommentModeration(
            comment_id=comment.id,
            content_version=data.version,
            verdict=data.verdict,
            judge=data.judge,
            reason=data.reason,
            scores=data.scores,
        )
        await self.repo.save_verdict(comment, moderation)
        return ModerationVerdictResult(result="applied")

    async def get_queue(
        self,
        status_filter: ModerationStatus | None,
        page: int,
        limit: int,
    ) -> AdminModerationCommentQueuePagination:
        offset = (page - 1) * limit
        comments, total = await self.repo.get_moderation_queue(
            status_filter=status_filter,
            offset=offset,
            limit=limit,
        )
        items = [self._to_admin_comment_item(c) for c in comments]
        total_pages = (total - 1 + limit) // limit if total > 0 else 0
        return AdminModerationCommentQueuePagination(
            items=items,
            page=page,
            total=total,
            total_pages=total_pages,
        )

    async def get_history(self, comment_id: uuid.UUID) -> list[CommentModerationHistoryItem]:
        await self.comment_service.get_by_id(comment_id)
        records = await self.repo.get_history_by_comment_id(comment_id)
        return [CommentModerationHistoryItem.model_validate(r) for r in records]

    async def decide(
        self,
        comment_id: uuid.UUID,
        data: AdminDecisionRequest,
        admin_user: User,
    ) -> AdminModerationCommentItem:
        comment = await self.comment_service.get_by_id(comment_id)
        if data.version != comment.content_version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Comment content was modified by the author. Please reload.",
            )

        if data.decision == "approve":
            verdict = Verdict.APPROVE
            new_status = ModerationStatus.APPROVED
            reason = None
        else:
            verdict = Verdict.REJECT
            new_status = ModerationStatus.REJECTED
            reason = data.reason or comment.moderation_reason or "policy_violation"

        comment.moderation_status = new_status
        comment.moderation_reason = reason
        comment.moderated_version = comment.content_version

        moderation = CommentModeration(
            comment_id=comment.id,
            content_version=comment.content_version,
            verdict=verdict,
            judge=Judge.ADMIN,
            reason=reason,
            scores={},
            admin_id=admin_user.id,
            note=data.note,
        )
        updated_comment = await self.repo.save_verdict(comment, moderation)
        return self._to_admin_comment_item(updated_comment)

    @staticmethod
    def _to_admin_comment_item(comment: Comment) -> AdminModerationCommentItem:
        sorted_mods = sorted(
            comment.moderations or [],
            key=lambda m: m.created_at,
            reverse=True,
        )
        latest = (
            CommentModerationHistoryItem.model_validate(sorted_mods[0]) if sorted_mods else None
        )
        is_appeal = any(
            m.content_version == comment.content_version and m.judge == Judge.USER_APPEAL
            for m in sorted_mods
        )
        return AdminModerationCommentItem.model_validate(
            comment,
            update={
                "latest_moderation": latest,
                "is_appeal": is_appeal,
            },
        )
