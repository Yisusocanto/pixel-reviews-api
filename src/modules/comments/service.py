import logging
import uuid
from datetime import UTC, datetime

from fastapi import BackgroundTasks, HTTPException, status

from src.modules.comment_moderation.models import CommentModeration
from src.modules.comments.models import Comment, CommentCreate, CommentUpdate
from src.modules.comments.repository import CommentRepository
from src.modules.comments.schemas import CommentPagination, CommentResponse
from src.modules.reviews.service import ReviewService
from src.schemas.moderation import Judge, ModerationStatus, Verdict
from src.services.moderation_producer.client import ModerationProducer
from src.services.moderation_producer.schemas import ModerationPayload, ModerationType

logger = logging.getLogger("comment_service")


class CommentService:
    def __init__(
        self,
        repo: CommentRepository,
        review_service: ReviewService,
        moderation_producer: ModerationProducer,
    ):
        self.repo = repo
        self.review_service = review_service
        self.moderation_producer = moderation_producer

    async def create(
        self, data: CommentCreate, user_id: uuid.UUID, bg_tasks: BackgroundTasks
    ) -> CommentResponse:
        await self.review_service.get_by_id(data.review_id)

        if not data.content or not data.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Content cannot be empty"
            )

        comment = Comment(
            **data.model_dump(),
            user_id=user_id,
            moderation_status=ModerationStatus.PENDING,
            moderation_enqueued_at=datetime.now(UTC),
        )
        new_comment = await self.repo.add(comment)

        payload = ModerationPayload(
            id=new_comment.id,
            version=new_comment.content_version,
            type=ModerationType.COMMENT,
            content=new_comment.content,
        )
        bg_tasks.add_task(
            self.moderation_producer.publish,
            routing_key="moderation.comment.check",
            payload=payload,
        )
        logger.info(
            "[COMMENTS] Enqueued comment %s (v%s) for moderation",
            new_comment.id,
            new_comment.content_version,
        )
        return self._to_comment_response(new_comment, user_id)

    async def get_by_id(self, comment_id: uuid.UUID) -> Comment:
        comment = await self.repo.get_by_id(comment_id)
        if not comment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
        return comment

    async def get_all(
        self,
        page: int,
        limit: int,
        review_id: uuid.UUID,
        current_user_id: uuid.UUID | None = None,
    ) -> CommentPagination:
        offset = (page - 1) * limit
        comments = await self.repo.get_all(
            offset=offset,
            limit=limit,
            review_id=review_id,
            current_user_id=current_user_id,
        )
        total = await self.repo.count_all(
            review_id=review_id,
            current_user_id=current_user_id,
        )
        total_pages = (total - 1 + limit) // limit if total > 0 else 0
        items = [self._to_comment_response(c, current_user_id) for c in comments]

        return CommentPagination(
            items=items,
            total=total,
            total_pages=total_pages,
            page=page,
        )

    async def update(
        self,
        comment_id: uuid.UUID,
        user_id: uuid.UUID,
        new_data: CommentUpdate,
        bg_tasks: BackgroundTasks,
    ) -> CommentResponse:
        comment = await self.get_by_id(comment_id)
        if comment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed")

        updated_data = new_data.model_dump(exclude_unset=True)
        new_content = updated_data.get("content", comment.content)

        if "content" in updated_data and (not new_content or not new_content.strip()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Content cannot be empty"
            )

        if new_content != comment.content:
            comment.content_version += 1
            comment.moderation_enqueued_at = datetime.now(UTC)
            comment.moderation_status = (
                ModerationStatus.PENDING
                if comment.moderation_status != ModerationStatus.REJECTED
                else ModerationStatus.REJECTED
            )
            payload = ModerationPayload(
                id=comment.id,
                version=comment.content_version,
                type=ModerationType.COMMENT,
                content=new_content,
            )
            bg_tasks.add_task(
                self.moderation_producer.publish,
                routing_key="moderation.comment.check",
                payload=payload,
            )
            logger.info(
                "[COMMENTS] Comment %s edited to v%s; enqueued for moderation (status=%s)",
                comment.id,
                comment.content_version,
                comment.moderation_status,
            )
        comment.sqlmodel_update(updated_data)
        updated_comment = await self.repo.add(comment)
        return self._to_comment_response(updated_comment, user_id)

    async def appeal(self, comment_id: uuid.UUID, user_id: uuid.UUID) -> CommentResponse:
        comment = await self.get_by_id(comment_id)
        if comment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed")

        moderation_info = self._get_moderation_info(comment, user_id)
        if not moderation_info or not moderation_info["can_appeal"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This comment cannot be appealed.",
            )

        comment.moderation_status = ModerationStatus.NEEDS_REVIEW
        appeal_record = CommentModeration(
            comment_id=comment.id,
            content_version=comment.content_version,
            verdict=Verdict.DOUBT,
            judge=Judge.USER_APPEAL,
            reason=comment.moderation_reason,
            scores={},
        )
        updated_comment = await self.repo.save_appeal(comment, appeal_record)
        logger.info(
            "[COMMENTS] User %s appealed comment %s (v%s)",
            user_id,
            comment.id,
            comment.content_version,
        )
        return self._to_comment_response(updated_comment, user_id)

    async def delete(self, comment_id: uuid.UUID, user_id: uuid.UUID) -> Comment:
        comment = await self.get_by_id(comment_id)
        if comment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not allowed")

        return await self.repo.delete(comment)

    @classmethod
    def _to_comment_response(
        cls, comment: Comment, current_user_id: uuid.UUID | None
    ) -> CommentResponse:
        return CommentResponse.model_validate(
            comment,
            update={
                "moderation": cls._get_moderation_info(comment, current_user_id),
            },
        )

    @staticmethod
    def _get_moderation_info(comment: Comment, current_user_id: uuid.UUID | None):
        if current_user_id is not None and comment.user_id == current_user_id:
            already_appealed_or_decided = any(
                m.content_version == comment.content_version
                and m.judge in (Judge.USER_APPEAL, Judge.ADMIN)
                for m in (comment.moderations or [])
            )
            can_appeal = (
                comment.moderation_status == ModerationStatus.REJECTED
                and comment.content_version == comment.moderated_version
                and not already_appealed_or_decided
            )
            return {
                "status": comment.moderation_status,
                "reason": comment.moderation_reason,
                "can_appeal": can_appeal,
            }
        return None
