import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from src.core.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.modules.games.models import Game
    from src.modules.users.models import User


class ReviewBase(SQLModel):
    title: str
    content: str
    game_id: uuid.UUID = Field(foreign_key="game.id", ondelete="CASCADE")


class Review(ReviewBase, TimestampMixin, table=True):
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")

    user: "User" = Relationship(  # noqa: UP037
        back_populates="reviews"
    )
    game: "Game" = Relationship(  # noqa: UP037
        back_populates="reviews"
    )

    __table_args__ = (UniqueConstraint("user_id", "game_id", name="uq_user_game"),)


class ReviewCreate(ReviewBase):
    pass
