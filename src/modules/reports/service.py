import uuid

from fastapi import HTTPException, status

from src.modules.comments.models import Comment
from src.modules.comments.service import CommentService
from src.modules.reports.models import CreateReport, Report, ReportStatus, TargetType
from src.modules.reports.repository import ReportRepository
from src.modules.reports.schemas import (
    AdminReportItem,
    AdminReportPagination,
    ReportedTargetPreview,
    ReportVerdictRequest,
)
from src.modules.reviews.models import Review
from src.modules.reviews.service import ReviewService
from src.modules.users.models import UserResponse
from src.schemas.moderation import ModerationStatus


class ReportService:
    def __init__(
        self, repo: ReportRepository, review_service: ReviewService, comment_service: CommentService
    ) -> None:
        self.repo = repo
        self.review_service = review_service
        self.comment_service = comment_service

    async def create(self, data: CreateReport, user_id: uuid.UUID) -> Report:
        if data.target_type == TargetType.COMMENT:
            target: Review | Comment = await self.comment_service.get_by_id(data.target_id)
        else:
            target = await self.review_service.get_by_id(data.target_id)

        if target.user_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot report your own content",
            )

        existing = await self.repo.get_by_reporter_and_target(
            reporter_id=user_id,
            target_type=data.target_type,
            target_id=data.target_id,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reported this content",
            )

        if data.target_type == TargetType.COMMENT:
            await self.comment_service.update_moderation_status(
                target, ModerationStatus.NEEDS_REVIEW
            )
        else:
            await self.review_service.update_moderation_status(
                target, ModerationStatus.NEEDS_REVIEW
            )

        report = Report(**data.model_dump(exclude_unset=True), reporter_id=user_id)
        return await self.repo.add(report)

    async def get_queue(
        self,
        status_filter: ReportStatus | None,
        target_type_filter: TargetType | None,
        page: int,
        limit: int,
    ) -> AdminReportPagination:
        offset = (page - 1) * limit
        reports, total = await self.repo.get_queue(
            status_filter=status_filter,
            target_type_filter=target_type_filter,
            offset=offset,
            limit=limit,
        )

        review_ids = [r.target_id for r in reports if r.target_type == TargetType.REVIEW]
        comment_ids = [r.target_id for r in reports if r.target_type == TargetType.COMMENT]
        all_target_ids = list({r.target_id for r in reports})

        reviews_map = await self.repo.get_reviews_by_ids(review_ids)
        comments_map = await self.repo.get_comments_by_ids(comment_ids)
        open_counts = await self.repo.count_open_by_targets(all_target_ids)

        items = [
            self._to_admin_report_item(
                report=r,
                reviews_map=reviews_map,
                comments_map=comments_map,
                open_reports_count=open_counts.get((r.target_type, r.target_id), 0),
            )
            for r in reports
        ]

        total_pages = (total - 1 + limit) // limit if total > 0 else 0
        return AdminReportPagination(
            items=items,
            total=total,
            total_pages=total_pages,
            page=page,
        )

    async def apply_verdict(
        self, report_id: uuid.UUID, data: ReportVerdictRequest
    ) -> AdminReportItem:
        report = await self.repo.get_by_id(report_id)
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

        if report.status != ReportStatus.OPEN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This report has already been resolved or dismissed",
            )

        match data.status:
            case ReportStatus.DISMISSED:
                await self._apply_new_status(report, ModerationStatus.APPROVED)
            case ReportStatus.RESOLVED:
                await self._apply_new_status(report, ModerationStatus.REJECTED)
            case _:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only Resolved and Dismissed status are allowed",
                )

        await self.repo.update_open_status_for_target(
            target_type=report.target_type,
            target_id=report.target_id,
            new_status=data.status,
        )
        updated_report = await self.repo.get_by_id(report.id)
        if not updated_report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

        reviews_map = (
            await self.repo.get_reviews_by_ids([updated_report.target_id])
            if updated_report.target_type == TargetType.REVIEW
            else {}
        )
        comments_map = (
            await self.repo.get_comments_by_ids([updated_report.target_id])
            if updated_report.target_type == TargetType.COMMENT
            else {}
        )
        return self._to_admin_report_item(
            report=updated_report,
            reviews_map=reviews_map,
            comments_map=comments_map,
            open_reports_count=0,
        )

    async def _apply_new_status(self, report: Report, new_status: ModerationStatus) -> None:
        if report.target_type == TargetType.COMMENT:
            target = await self.comment_service.get_by_id(report.target_id)
            await self.comment_service.update_moderation_status(target, new_status)
        else:
            target = await self.review_service.get_by_id(report.target_id)
            await self.review_service.update_moderation_status(target, new_status)

    def _to_admin_report_item(
        self,
        report: Report,
        reviews_map: dict[uuid.UUID, Review],
        comments_map: dict[uuid.UUID, Comment],
        open_reports_count: int,
    ) -> AdminReportItem:
        target_preview: ReportedTargetPreview | None = None

        if report.target_type == TargetType.REVIEW:
            review = reviews_map.get(report.target_id)
            if review:
                target_preview = ReportedTargetPreview(
                    id=review.id,
                    target_type=TargetType.REVIEW,
                    title=review.title,
                    content=review.content,
                    moderation_status=review.moderation_status,
                    author=UserResponse.model_validate(review.user),
                    game_title=review.game.title if review.game else None,
                    game_slug=review.game.slug if review.game else None,
                )
        else:
            comment = comments_map.get(report.target_id)
            if comment:
                game = comment.review.game if comment.review else None
                target_preview = ReportedTargetPreview(
                    id=comment.id,
                    target_type=TargetType.COMMENT,
                    title=comment.review.title if comment.review else None,
                    content=comment.content,
                    moderation_status=comment.moderation_status,
                    author=UserResponse.model_validate(comment.user),
                    game_title=game.title if game else None,
                    game_slug=game.slug if game else None,
                    review_id=comment.review_id,
                )

        return AdminReportItem(
            id=report.id,
            target_id=report.target_id,
            target_type=report.target_type,
            type=report.type,
            reason=report.reason,
            reporter_id=report.reporter_id,
            status=report.status,
            created_at=report.created_at,
            updated_at=report.updated_at,
            reporter=UserResponse.model_validate(report.reporter),
            target=target_preview,
            open_reports_count=open_reports_count,
        )
