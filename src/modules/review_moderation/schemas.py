import uuid
from typing import Literal

from pydantic import Field

from src.core.mixins import TimestampMixin
from src.modules.review_moderation.models import Judge, ReviewModerationBase, Verdict
from src.modules.reviews.models import ReviewBase
from src.modules.users.models import UserResponse
from src.schemas.config_base import ConfigBase
from src.services.moderation_producer.schemas import ModerationType


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
