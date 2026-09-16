from pydantic import BaseModel, Field

from src.modules.developers.models import DeveloperCreate
from src.modules.publisher.models import PublisherCreate


class GameSearchRawgResponse(BaseModel):
    title: str
    slug: str
    release_date: str | None = None
    background_image: str | None = None


class GameDetailRawgResponse(BaseModel):
    rawg_id: int
    title: str
    slug: str
    description: str | None = None
    release_date: str | None = None
    image_url: str | None = None
    screenshots: list[str] = []
    developers: list[DeveloperCreate] = Field(default_factory=list)
    publishers: list[PublisherCreate] = Field(default_factory=list)
