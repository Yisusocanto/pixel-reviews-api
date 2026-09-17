import uuid

from src.modules.games.models import Game
from src.modules.reviews.models import ReviewBase
from src.modules.users.models import UserResponse
from src.schemas.pagination import Pagination


class ReviewResponse(ReviewBase):
    id: uuid.UUID
    user_id: uuid.UUID

    user: UserResponse
    game: Game


class ReviewPagination(Pagination):
    items: list[ReviewResponse]
