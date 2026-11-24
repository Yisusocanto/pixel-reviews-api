import uuid

from sqlalchemy import func, update
from sqlalchemy.orm import selectinload
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.comments.models import Comment
from src.modules.reports.models import Report, ReportStatus, TargetType
from src.modules.reviews.models import Review


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, report: Report) -> Report:
        self.session.add(report)
        await self.session.flush()
        new_report = await self.get_by_id(report.id)
        return new_report or report

    async def get_by_id(self, report_id: uuid.UUID) -> Report | None:
        stmt = select(Report).where(Report.id == report_id).options(selectinload(Report.reporter))
        result = await self.session.exec(stmt)
        return result.first()

    async def get_by_reporter_and_target(
        self,
        reporter_id: uuid.UUID,
        target_type: TargetType,
        target_id: uuid.UUID,
    ) -> Report | None:
        stmt = select(Report).where(
            Report.reporter_id == reporter_id,
            Report.target_type == target_type,
            Report.target_id == target_id,
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_queue(
        self,
        status_filter: ReportStatus | None,
        target_type_filter: TargetType | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Report], int]:
        count_stmt = select(func.count()).select_from(Report)
        stmt = select(Report).options(selectinload(Report.reporter))

        if status_filter is not None:
            count_stmt = count_stmt.where(Report.status == status_filter)
            stmt = stmt.where(Report.status == status_filter)

        if target_type_filter is not None:
            count_stmt = count_stmt.where(Report.target_type == target_type_filter)
            stmt = stmt.where(Report.target_type == target_type_filter)

        total_result = await self.session.exec(count_stmt)
        total = total_result.one()

        stmt = stmt.order_by(col(Report.created_at).desc()).offset(offset).limit(limit)
        result = await self.session.exec(stmt)
        return list(result.all()), total

    async def count_open_by_targets(
        self,
        target_ids: list[uuid.UUID],
    ) -> dict[tuple[TargetType, uuid.UUID], int]:
        if not target_ids:
            return {}

        stmt = (
            select(Report.target_type, Report.target_id, func.count())
            .where(
                Report.status == ReportStatus.OPEN,
                col(Report.target_id).in_(target_ids),
            )
            .group_by(Report.target_type, Report.target_id)
        )
        result = await self.session.exec(stmt)
        return {(row[0], row[1]): int(row[2]) for row in result.all()}

    async def get_reviews_by_ids(self, review_ids: list[uuid.UUID]) -> dict[uuid.UUID, Review]:
        if not review_ids:
            return {}

        stmt = (
            select(Review)
            .where(col(Review.id).in_(review_ids))
            .options(selectinload(Review.user), selectinload(Review.game))
        )
        result = await self.session.exec(stmt)
        return {review.id: review for review in result.all()}

    async def get_comments_by_ids(self, comment_ids: list[uuid.UUID]) -> dict[uuid.UUID, Comment]:
        if not comment_ids:
            return {}

        stmt = (
            select(Comment)
            .where(col(Comment.id).in_(comment_ids))
            .options(
                selectinload(Comment.user),
                selectinload(Comment.review).selectinload(Review.game),
            )
        )
        result = await self.session.exec(stmt)
        return {comment.id: comment for comment in result.all()}

    async def update_open_status_for_target(
        self,
        target_type: TargetType,
        target_id: uuid.UUID,
        new_status: ReportStatus,
    ) -> None:
        stmt = (
            update(Report)
            .where(
                Report.target_type == target_type,
                Report.target_id == target_id,
                Report.status == ReportStatus.OPEN,
            )
            .values(status=new_status)
        )
        await self.session.exec(stmt)
        await self.session.flush()
