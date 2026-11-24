from fastapi import APIRouter, status

from src.modules.auth.dependencies import CurrentUserDep
from src.modules.reports.dependencies import ReportServiceDep
from src.modules.reports.models import CreateReport
from src.modules.reports.schemas import ReportResponse

router = APIRouter(prefix="/reports", tags=["Content Reports"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(service: ReportServiceDep, user: CurrentUserDep, data: CreateReport):
    return await service.create(data, user.id)
