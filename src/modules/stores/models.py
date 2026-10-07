import uuid
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.modules.games.models import Game


class GameStoreLink(SQLModel, table=True):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    game_id: uuid.UUID = Field(foreign_key="game.id", primary_key=True)
    store_id: uuid.UUID = Field(foreign_key="store.id", primary_key=True)

    __table_args__ = (UniqueConstraint("game_id", "store_id", name="uq_game_store"),)


class StoreBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    name: str
    slug: str = Field(unique=True, index=True)
    domain: str
    url: str | None


class Store(StoreBase, table=True):
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)

    games: list["Game"] = Relationship(  # noqa: UP037
        back_populates="stores",
        link_model=GameStoreLink,
    )


class StoreCreate(StoreBase):
    pass
