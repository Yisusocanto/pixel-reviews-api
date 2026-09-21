import uuid
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from src.core.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.modules.games.models import Game
    from src.modules.users.models import User


class WishlistBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    game_id: uuid.UUID = Field(foreign_key="game.id", ondelete="CASCADE")


class Wishlist(WishlistBase, TimestampMixin, table=True):
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")

    game: "Game" = Relationship(  # noqa: UP037
        back_populates="wishlist",
    )
    user: "User" = Relationship(  # noqa: UP037
        back_populates="wishlist",
    )

    __table_args__ = (UniqueConstraint("game_id", "user_id", name="uq_game_user"),)


class WishlistCreate(WishlistBase):
    pass
