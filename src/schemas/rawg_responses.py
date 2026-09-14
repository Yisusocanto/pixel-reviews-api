from pydantic import BaseModel


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
