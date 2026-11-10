from pydantic import Field

from src.schemas.config_base import ConfigBase


class AddFavUserGamesRequest(ConfigBase):
    games_slugs: list[str] = Field(min_length=0, max_length=5)
