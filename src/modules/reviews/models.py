import uuid
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from src.core.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.modules.games.models import Game
    from src.modules.users.models import User


class ReviewBase(SQLModel):
    title: str | None = None
    content: str | None = None
    score: int = Field(ge=1, le=5)
    game_id: uuid.UUID = Field(foreign_key="game.id", ondelete="CASCADE")


class Review(ReviewBase, TimestampMixin, table=True):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")

    user: "User" = Relationship(  # noqa: UP037
        back_populates="reviews"
    )
    game: "Game" = Relationship(  # noqa: UP037
        back_populates="reviews"
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
