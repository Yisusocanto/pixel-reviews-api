import uuid

from src.developers.models import Developer
from src.games.models import GameBase
from src.publisher.models import Publisher
from src.schemas.pagination import Pagination


class GameResponse(GameBase):
    id: uuid.UUID
    developers: list[Developer]
    publishers: list[Publisher]

class GamePagination(Pagination):
    items: list[GameResponse]

