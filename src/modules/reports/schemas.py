import uuid
from datetime import datetime

from src.modules.reports.models import ReportBase, ReportStatus, TargetType
from src.modules.users.models import UserResponse
from src.schemas.config_base import ConfigBase
from src.schemas.moderation import ModerationStatus


class ReportResponse(ReportBase):
    id: uuid.UUID
    reporter_id: uuid.UUID
    status: ReportStatus
    created_at: datetime
    updated_at: datetime
    reporter: UserResponse


class ReportedTargetPreview(ConfigBase):
    id: uuid.UUID
    target_type: TargetType
    title: str | None = None
    content: str | None = None
    moderation_status: ModerationStatus
    author: UserResponse
    game_title: str | None = None
    game_slug: str | None = None
    review_id: uuid.UUID | None = None


class AdminReportItem(ReportResponse):
    target: ReportedTargetPreview | None = None
    open_reports_count: int = 0


class AdminReportPagination(ConfigBase):
    items: list[AdminReportItem]
    total: int
    total_pages: int
    page: int


class ReportVerdictRequest(ConfigBase):
    status: ReportStatus
