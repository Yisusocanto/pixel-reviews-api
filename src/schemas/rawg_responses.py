from pydantic import Field

from src.modules.developers.models import DeveloperCreate
from src.modules.publisher.models import PublisherCreate
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
    release_date: str | None = None
    image_url: str | None = None
    background_image: str | None = None
    screenshots: list[str] = Field(default=list)
    developers: list[DeveloperCreate] = Field(default_factory=list)
    publishers: list[PublisherCreate] = Field(default_factory=list)
