import uuid
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.modules.genres.models import Game


class GamePlatformLink(SQLModel, table=True):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    game_id: uuid.UUID = Field(primary_key=True, foreign_key="game.id")
    platform_id: uuid.UUID = Field(primary_key=True, foreign_key="platform.id")


class PlatformBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    slug: str = Field(unique=True, index=True)
    name: str


class Platform(PlatformBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    games: list["Game"] = Relationship(  # noqa: UP037
        back_populates="platforms", link_model=GamePlatformLink
    )


class PlatformCreate(PlatformBase):
    pass
