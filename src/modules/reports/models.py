import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import String, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from src.core.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.modules.users.models import User


class TargetType(StrEnum):
    REVIEW = "review"
    COMMENT = "comment"


class ReportType(StrEnum):
    SPAM = "spam"
    SPOILER = "spoiler"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    INAPPROPRIATE = "inappropriate"
    OFF_TOPIC = "off_topic"
    OTHER = "other"


class ReportStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ReportBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )
    target_id: uuid.UUID = Field(index=True)
    target_type: TargetType = Field(sa_type=String(), nullable=False)
    type: ReportType = Field(sa_type=String(), nullable=False)
    reason: str | None = Field(default=None, max_length=500)


class Report(ReportBase, TimestampMixin, table=True):
    __tablename__ = "report"
    __table_args__ = (
        UniqueConstraint(
            "reporter_id",
            "target_type",
            "target_id",
            name="uq_report_reporter_target",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    reporter_id: uuid.UUID = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    status: ReportStatus = Field(
        default=ReportStatus.OPEN, sa_type=String(), nullable=False, index=True
    )

    reporter: "User" = Relationship(back_populates="reports")  # noqa: UP037


class CreateReport(ReportBase):
    pass
