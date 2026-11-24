import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.modules.auth.dependencies import require_admin
from src.modules.reports.dependencies import ReportServiceDep
from src.modules.reports.models import ReportStatus, TargetType
from src.modules.reports.schemas import (
    AdminReportItem,
    AdminReportPagination,
    ReportVerdictRequest,
)

router = APIRouter(
    prefix="/admin/moderation/reports",
    tags=["Admin Moderation"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=AdminReportPagination)
async def get_reports_queue(
    service: ReportServiceDep,
    status: Annotated[ReportStatus | None, Query()] = ReportStatus.OPEN,
    target_type: Annotated[TargetType | None, Query(alias="targetType")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    return await service.get_queue(
        status_filter=status,
        target_type_filter=target_type,
        page=page,
        limit=limit,
    )


@router.post("/{report_id}/verdict", response_model=AdminReportItem)
async def apply_report_verdict(
    report_id: uuid.UUID,
    data: ReportVerdictRequest,
    service: ReportServiceDep,
):
    return await service.apply_verdict(report_id=report_id, data=data)
