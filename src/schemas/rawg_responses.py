from pydantic import Field

from src.modules.developers.models import DeveloperCreate
from src.modules.genres.models import GenreCreate
from src.modules.platforms.models import PlatformCreate
from src.modules.publisher.models import PublisherCreate
from src.modules.stores.models import StoreCreate
from src.schemas.config_base import ConfigBase


class GameSearchRawgResponse(ConfigBase):
    title: str
    slug: str
    release_date: str | None = None
    background_image: str | None = None


class GameDetailRawgResponse(ConfigBase):
    rawg_id: int
    title: str
    slug: str
    description: str | None = None
    metacritic_score: int | None
    metacritic_url: str | None
    website: str | None
    release_date: str | None = None
    image_url: str | None = None
    background_image: str | None = None
    screenshots: list[str] = Field(default=list)
    developers: list[DeveloperCreate] = Field(default_factory=list)
    publishers: list[PublisherCreate] = Field(default_factory=list)
    stores: list[StoreCreate] = Field(default_factory=list)
    genres: list[GenreCreate] = Field(default_factory=list)
    platforms: list[PlatformCreate] = Field(default_factory=list)
