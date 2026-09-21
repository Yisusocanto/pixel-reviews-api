import uuid
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.modules.games.models import Game


class GameDeveloperLink(SQLModel, table=True):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    game_id: uuid.UUID = Field(primary_key=True, foreign_key="game.id")
    developer_id: uuid.UUID = Field(primary_key=True, foreign_key="developer.id")


class DeveloperBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    rawg_id: int = Field(index=True, unique=True)
    name: str = Field(index=True)
    slug: str = Field(index=True, unique=True)


class Developer(DeveloperBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    games: list["Game"] = Relationship(back_populates="developers", link_model=GameDeveloperLink)  # noqa: UP037


class DeveloperCreate(DeveloperBase):
    pass
