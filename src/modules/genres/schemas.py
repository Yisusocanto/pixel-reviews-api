from src.modules.games.schemas import GameResponse
from src.modules.genres.models import Genre
from src.schemas.pagination import Pagination


class GenreGamesPagination(Pagination):
    genre: Genre
    items: list[GameResponse]
