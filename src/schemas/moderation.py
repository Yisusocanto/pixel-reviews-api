import uuid
from enum import StrEnum
from typing import Literal

from pydantic import Field

from src.schemas.config_base import ConfigBase
from src.services.moderation_producer.schemas import ModerationType


class Verdict(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    DOUBT = "doubt"


class Judge(StrEnum):
    RULES = "rules"
    AI_MODEL = "ai_model"
    ADMIN = "admin"
    SYSTEM = "system"
    USER_APPEAL = "user_appeal"


class ModerationVerdictResult(ConfigBase):
    result: Literal["applied", "stale", "duplicate"]


class ModerationVerdictRequest(ConfigBase):
    id: uuid.UUID
    type: ModerationType
    version: int
    judge: Judge
    reason: str | None = None
    verdict: Verdict
    scores: dict[str, float] = Field(default_factory=dict)


class AdminDecisionRequest(ConfigBase):
    decision: Literal["approve", "reject"]
    version: int
    reason: str | None = None
    note: str | None = None


class ModerationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class ModerationInfo(ConfigBase):
    status: ModerationStatus
    reason: str | None
    can_appeal: bool = False


VERDICT_STATUS_MAP: dict[Verdict, ModerationStatus] = {
    Verdict.REJECT: ModerationStatus.REJECTED,
    Verdict.APPROVE: ModerationStatus.APPROVED,
    Verdict.DOUBT: ModerationStatus.NEEDS_REVIEW,
}
