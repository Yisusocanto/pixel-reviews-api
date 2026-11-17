import uuid

from src.core.mixins import TimestampMixin
from src.modules.games.models import Game
from src.modules.reviews.models import ModerationStatus, ReviewBase
from src.modules.users.models import UserResponse
from src.schemas.config_base import ConfigBase
from src.schemas.pagination import Pagination


class ModerationInfo(ConfigBase):
    status: ModerationStatus
    reason: str | None
    can_appeal: bool = False


class ReviewResponse(ReviewBase, TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    likes_count: int = 0
    liked_by_user: bool = False
    comments_count: int = 0
    moderation: ModerationInfo | None = None

    user: UserResponse
    game: Game


class ReviewPagination(Pagination):
    items: list[ReviewResponse]
