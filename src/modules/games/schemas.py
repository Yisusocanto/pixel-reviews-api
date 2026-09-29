import uuid

from src.modules.developers.models import Developer
from src.modules.games.models import GameBase
from src.modules.publisher.models import Publisher
from src.schemas.config_base import ConfigBase
from src.schemas.pagination import Pagination


class GameResponse(GameBase):
    id: uuid.UUID
    developers: list[Developer]
    publishers: list[Publisher]


class GamePagination(Pagination):
    items: list[GameResponse]


class GameStats(ConfigBase):
    total_reviews: int
    avg_ratings: float
    rating_distribution: list[dict[str, float]]
