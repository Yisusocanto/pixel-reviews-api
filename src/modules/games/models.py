import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, Relationship, SQLModel

from src.modules.developers.models import GameDeveloperLink
from src.modules.genres.models import GameGenreLink
from src.modules.platforms.models import GamePlatformLink
from src.modules.publisher.models import GamePublisherLink
from src.modules.stores.models import GameStoreLink, StoreRead

if TYPE_CHECKING:
    from src.modules.developers.models import Developer
    from src.modules.genres.models import Genre
    from src.modules.platforms.models import Platform
    from src.modules.publisher.models import Publisher
    from src.modules.reviews.models import Review
    from src.modules.wishlists.models import Wishlist


class GameBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    title: str = Field(index=True)
    slug: str = Field(index=True, unique=True)
    igdb_id: int = Field(index=True, unique=True)
    release_date: datetime | None = None
    image_url: str
    background_image: str | None = None
    description: str = ""
    storyline: str | None = None
    critic_score: int | None = None
    critic_score_count: int | None = None
    igdb_url: str | None = None
    website: str | None = None
    trailer_youtube_id: str | None = None
    trailer_title: str | None = None
    screenshots: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String), nullable=False, server_default="{}")
    )
    game_modes: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String), nullable=False, server_default="{}")
    )
    themes: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String), nullable=False, server_default="{}")
    )
    player_perspectives: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String), nullable=False, server_default="{}")
    )


class Game(GameBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)

    developers: list[Developer] = Relationship(back_populates="games", link_model=GameDeveloperLink)
    publishers: list[Publisher] = Relationship(back_populates="games", link_model=GamePublisherLink)
    reviews: list[Review] = Relationship(
        back_populates="game", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    wishlist: list[Wishlist] = Relationship(
        back_populates="game",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    store_links: list[GameStoreLink] = Relationship(
        back_populates="game",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    genres: list[Genre] = Relationship(back_populates="games", link_model=GameGenreLink)
    platforms: list[Platform] = Relationship(back_populates="games", link_model=GamePlatformLink)

    @property
    def stores(self) -> list[StoreRead]:
        return [
            StoreRead(
                id=link.store.id,
                name=link.store.name,
                slug=link.store.slug,
                domain=link.store.domain,
                url=link.url,
            )
            for link in self.store_links
            if link.store is not None
        ]


class GameCreate(GameBase):
    pass
