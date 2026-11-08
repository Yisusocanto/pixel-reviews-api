from datetime import datetime

from pydantic import Field

from src.modules.developers.models import DeveloperCreate
from src.modules.genres.models import GenreCreate
from src.modules.platforms.models import PlatformCreate
from src.modules.publisher.models import PublisherCreate
from src.modules.stores.models import StoreCreate
from src.schemas.config_base import ConfigBase
from src.schemas.pagination import Pagination


class GameSearchIgdbResponse(ConfigBase):
    title: str
    slug: str
    release_date: str | None = None
    image_url: str | None = None
    background_image: str | None = None
    critic_score: int | None = None


class GameSearchPagination(Pagination):
    items: list[GameSearchIgdbResponse]


class GameDetailIgdbResponse(ConfigBase):
    igdb_id: int
    title: str
    slug: str
    description: str = ""
    storyline: str | None = None
    critic_score: int | None = None
    critic_score_count: int | None = None
    igdb_url: str | None = None
    website: str | None = None
    release_date: datetime | None = None
    image_url: str
    background_image: str | None = None
    trailer_youtube_id: str | None = None
    trailer_title: str | None = None
    screenshots: list[str] = Field(default_factory=list)
    game_modes: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    player_perspectives: list[str] = Field(default_factory=list)
    developers: list[DeveloperCreate] = Field(default_factory=list)
    publishers: list[PublisherCreate] = Field(default_factory=list)
    stores: list[StoreCreate] = Field(default_factory=list)
    genres: list[GenreCreate] = Field(default_factory=list)
    platforms: list[PlatformCreate] = Field(default_factory=list)
