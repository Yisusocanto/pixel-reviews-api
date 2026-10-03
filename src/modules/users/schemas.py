from src.modules.users.models import UserResponse
from src.schemas.config_base import ConfigBase
from src.schemas.pagination import Pagination


class UserPagination(Pagination):
    items: list[UserResponse]


class UserReviewStats(ConfigBase):
    avg_rating: float
    total_reviews: int
    total_ratings: int
    rating_distribution: list[dict[str, float]]


class UserStats(UserReviewStats):
    total_likes: int
