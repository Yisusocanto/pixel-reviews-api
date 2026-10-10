import uuid

from src.modules.developers.models import Developer
from src.modules.games.models import GameBase
from src.modules.genres.models import Genre
from src.modules.publisher.models import Publisher
from src.modules.stores.models import Store
from src.schemas.config_base import ConfigBase
from src.schemas.pagination import Pagination


class GameResponse(GameBase):
    id: uuid.UUID
    developers: list[Developer]
    publishers: list[Publisher]
    stores: list[Store]
    genres: list[Genre]


class GamePagination(Pagination):
    items: list[GameResponse]


class GameStats(ConfigBase):
    total_reviews: int
    avg_ratings: float
    rating_distribution: list[dict[str, float]]
