import uuid
from typing import TYPE_CHECKING, Optional

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import JSON, Column, String
from sqlmodel import Field, Relationship, SQLModel

from src.core.mixins import TimestampMixin
from src.schemas.moderation import Judge, Verdict

if TYPE_CHECKING:
    from src.modules.reviews.models import Review
    from src.modules.users.models import User


class ReviewModerationBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    review_id: uuid.UUID = Field(foreign_key="review.id", index=True, ondelete="CASCADE")
    content_version: int = Field(default=1)
    verdict: Verdict = Field(sa_type=String())
    judge: Judge = Field(sa_type=String())
    reason: str | None = None
    scores: dict[str, float] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )
    admin_id: uuid.UUID | None = Field(default=None, foreign_key="users.id", ondelete="SET NULL")
    note: str | None = None


class ReviewModeration(ReviewModerationBase, TimestampMixin, table=True):
    __tablename__ = "review_moderation"

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid7)

    review: "Review" = Relationship(back_populates="moderations")  # noqa: UP037
    admin: Optional["User"] = Relationship(back_populates="moderations")  # noqa: UP037, UP045
