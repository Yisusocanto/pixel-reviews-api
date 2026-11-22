from src.modules.games.models import Game
from src.modules.users.models import UserResponse
from src.schemas.config_base import ConfigBase


class TopWantedGame(ConfigBase):
    game: Game
    count: int


class TopRatedGame(ConfigBase):
    game: Game
    average: float
    count: int


class TopReviewedGame(ConfigBase):
    game: Game
    count: int
    last_week: int


class UserWithReviewCount(ConfigBase):
    user: UserResponse
    count: int
    last_week: int


class TotalReviews(ConfigBase):
    total: int
    last_week: float


class Statistics(ConfigBase):
    top_rated_games: list[TopRatedGame]
    top_reviewed_games: list[TopReviewedGame]
    top_wanted_games: list[TopWantedGame]
    top_users_with_the_most_reviews: list[UserWithReviewCount]
    total_reviews: TotalReviews
