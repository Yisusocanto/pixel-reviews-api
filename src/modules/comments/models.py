import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import DateTime, String
from sqlmodel import Field, Relationship, SQLModel

from src.core.mixins import TimestampMixin
from src.schemas.config_base import ConfigBase
from src.schemas.moderation import ModerationStatus

if TYPE_CHECKING:
    from src.modules.comment_moderation.models import CommentModeration
    from src.modules.reviews.models import Review
    from src.modules.users.models import User


class CommentBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    review_id: uuid.UUID = Field(foreign_key="review.id", index=True, ondelete="CASCADE")
    content: str


class Comment(CommentBase, TimestampMixin, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, ondelete="CASCADE")
    moderation_status: ModerationStatus = Field(
        default=ModerationStatus.PENDING, sa_type=String(), index=True
    )
    moderation_reason: str | None = None
    content_version: int = Field(default=1)
    moderated_version: int = Field(default=0)
    moderation_enqueued_at: datetime | None = Field(
        sa_type=DateTime(timezone=True), nullable=True, default=None
    )

    user: "User" = Relationship(back_populates="comments")  # noqa: UP037
    review: "Review" = Relationship(back_populates="comments")  # noqa: UP037
    moderations: list["CommentModeration"] = Relationship(  # noqa: UP037
        back_populates="comment", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class CommentCreate(CommentBase):
    pass


class CommentUpdate(ConfigBase):
    content: str | None = None
