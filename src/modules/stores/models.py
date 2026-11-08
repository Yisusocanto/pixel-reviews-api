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
    url: str | None = None

    game: Game = Relationship(back_populates="store_links")
    store: Store = Relationship(back_populates="game_links")

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


class Store(StoreBase, table=True):
    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid7)

    game_links: list[GameStoreLink] = Relationship(back_populates="store")


class StoreCreate(StoreBase):
    url: str | None = None


class StoreRead(StoreBase):
    id: uuid.UUID
    url: str | None = None
