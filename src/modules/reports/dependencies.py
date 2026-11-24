from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.comments.dependencies import CommentServiceDep
from src.modules.reports.repository import ReportRepository
from src.modules.reports.service import ReportService
from src.modules.reviews.dependencies import ReviewServiceDep


def get_report_repository(session: SessionDep) -> ReportRepository:
    return ReportRepository(session)


ReportRepositoryDep = Annotated[ReportRepository, Depends(get_report_repository)]


def get_report_service(
    repo: ReportRepositoryDep, review_service: ReviewServiceDep, comment_service: CommentServiceDep
):
    return ReportService(repo=repo, review_service=review_service, comment_service=comment_service)


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
