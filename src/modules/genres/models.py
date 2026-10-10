import uuid
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.modules.games.models import Game


class GameGenreLink(SQLModel, table=True):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    game_id: uuid.UUID = Field(primary_key=True, foreign_key="game.id")
    genre_id: uuid.UUID = Field(primary_key=True, foreign_key="genre.id")


class GenreBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    name: str
    slug: str = Field(index=True, unique=True)


class Genre(GenreBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    games: list["Game"] = Relationship(  # noqa: UP037
        back_populates="genres",
        link_model=GameGenreLink,
    )


class GenreCreate(GenreBase):
    pass
