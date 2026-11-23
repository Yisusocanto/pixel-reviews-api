import uuid

from src.core.mixins import TimestampMixin
from src.modules.games.models import Game
from src.modules.review_moderation.models import ReviewModerationBase
from src.modules.reviews.models import ReviewBase
from src.modules.users.models import UserResponse
from src.schemas.moderation import ModerationStatus
from src.schemas.pagination import Pagination


class ReviewModerationHistoryItem(ReviewModerationBase, TimestampMixin):
    id: uuid.UUID
    admin: UserResponse | None = None


class ReviewModerationResponse(ReviewModerationBase, TimestampMixin):
    id: uuid.UUID
    review: ReviewBase
    admin: UserResponse | None = None


class AdminModerationReviewItem(ReviewBase, TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    moderation_status: ModerationStatus
    moderation_reason: str | None = None
    content_version: int
    moderated_version: int
    user: UserResponse
    game: Game
    latest_moderation: ReviewModerationHistoryItem | None = None
    is_appeal: bool = False


class AdminModerationQueuePagination(Pagination):
    items: list[AdminModerationReviewItem]
