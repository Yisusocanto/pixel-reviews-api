import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import CheckConstraint, DateTime, String, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from src.core.mixins import TimestampMixin
from src.schemas.moderation import ModerationStatus

if TYPE_CHECKING:
    from src.modules.comments.models import Comment
    from src.modules.games.models import Game
    from src.modules.likes.models import Like
    from src.modules.review_moderation.models import ReviewModeration
    from src.modules.users.models import User


class ReviewBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    title: str | None = None
    content: str | None = None
    score: int = Field(ge=1, le=5)
    game_id: uuid.UUID = Field(foreign_key="game.id", ondelete="CASCADE")


class Review(ReviewBase, TimestampMixin, table=True):
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid7)
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    moderation_status: ModerationStatus = Field(
        default=ModerationStatus.PENDING, sa_type=String(), index=True
    )
    moderation_reason: str | None = None
    content_version: int = Field(default=1)
    moderated_version: int = Field(default=0)
    moderation_enqueued_at: datetime | None = Field(
        sa_type=DateTime(timezone=True), default=None, nullable=True
    )

    user: "User" = Relationship(  # noqa: UP037
        back_populates="reviews"
    )
    game: "Game" = Relationship(  # noqa: UP037
        back_populates="reviews"
    )
    likes: list["Like"] = Relationship(  # noqa: UP037
        back_populates="review", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    comments: list["Comment"] = Relationship(  # noqa: UP037
        back_populates="review", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    moderations: list["ReviewModeration"] = Relationship(  # noqa: UP037
        back_populates="review", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_user_game"),
        CheckConstraint("score >= 1 AND score <= 5", name="check_score"),
    )


class ReviewCreate(ReviewBase):
    pass


class ReviewUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    score: int | None = Field(ge=1, le=5, default=None)
