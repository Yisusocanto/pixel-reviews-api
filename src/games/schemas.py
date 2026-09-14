import uuid

from src.games.models import GameBase
from src.schemas.pagination import Pagination


class GameResponse(GameBase):
    id: uuid.UUID


class GamePagination(Pagination):
    items: list[GameResponse]
