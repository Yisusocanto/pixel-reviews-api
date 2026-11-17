import uuid
from typing import Literal

from pydantic import Field

from src.core.mixins import TimestampMixin
from src.modules.games.models import Game
from src.modules.review_moderation.models import Judge, ReviewModerationBase, Verdict
from src.modules.reviews.models import ModerationStatus, ReviewBase
from src.modules.users.models import UserResponse
from src.schemas.config_base import ConfigBase
from src.schemas.pagination import Pagination
from src.services.moderation_producer.schemas import ModerationType


class ReviewModerationHistoryItem(ReviewModerationBase, TimestampMixin):
    id: uuid.UUID
    admin: UserResponse | None = None


class ReviewModerationResponse(ReviewModerationBase, TimestampMixin):
    id: uuid.UUID
    review: ReviewBase
    admin: UserResponse | None = None


class ModerationVerdictRequest(ConfigBase):
    id: uuid.UUID
    type: ModerationType
    version: int
    judge: Judge
    reason: str | None = None
    verdict: Verdict
    scores: dict[str, float] = Field(default_factory=dict)


class ModerationVerdictResult(ConfigBase):
    result: Literal["applied", "stale", "duplicate"]


class AdminDecisionRequest(ConfigBase):
    decision: Literal["approve", "reject"]
    version: int
    reason: str | None = None
    note: str | None = None


class AdminModerationReviewItem(ReviewBase, TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    moderation_status: ModerationStatus
    moderation_reason: str | None = None
    content_version: int
    moderated_version: int
    user: UserResponse
    game: Game
    latest_moderation: ReviewModerationHistoryItem | None = None
    is_appeal: bool = False


class AdminModerationQueuePagination(Pagination):
    items: list[AdminModerationReviewItem]
