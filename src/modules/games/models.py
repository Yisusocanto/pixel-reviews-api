import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, Relationship, SQLModel

from src.modules.developers.models import GameDeveloperLink
from src.modules.publisher.models import GamePublisherLink

if TYPE_CHECKING:
    from src.modules.developers.models import Developer
    from src.modules.publisher.models import Publisher
    from src.modules.reviews.models import Review
    from src.modules.wishlists.models import Wishlist


class GameBase(SQLModel):
    title: str = Field(index=True)
    slug: str = Field(index=True, unique=True)
    rawg_id: int = Field(index=True, unique=True)
    release_date: datetime
    image_url: str
    description: str
    screenshots: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String), nullable=False, server_default="{}")
    )


class Game(GameBase, table=True):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    developers: list["Developer"] = Relationship(  # noqa: UP037
        back_populates="games", link_model=GameDeveloperLink
    )
    publishers: list["Publisher"] = Relationship(  # noqa: UP037
        back_populates="games", link_model=GamePublisherLink
    )
    reviews: list["Review"] = Relationship(  # noqa: UP037
        back_populates="game", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    wishlist: list["Wishlist"] = Relationship(  # noqa: UP037
        back_populates="game",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class GameCreate(GameBase):
    pass
