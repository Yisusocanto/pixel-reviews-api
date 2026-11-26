from src.modules.games.schemas import GameResponse
from src.modules.platforms.models import Platform
from src.schemas.pagination import Pagination


class PlatformGamesPagination(Pagination):
    platform: Platform
    items: list[GameResponse]
