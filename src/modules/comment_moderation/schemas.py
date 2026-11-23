import uuid

from src.core.mixins import TimestampMixin
from src.modules.comment_moderation.models import CommentModerationBase
from src.modules.comments.models import CommentBase
from src.modules.games.models import Game
from src.modules.users.models import UserResponse
from src.schemas.config_base import ConfigBase
from src.schemas.moderation import ModerationStatus
from src.schemas.pagination import Pagination


class CommentModerationHistoryItem(CommentModerationBase, TimestampMixin):
    id: uuid.UUID
    admin: UserResponse | None = None


class AdminModerationCommentReviewSummary(ConfigBase):
    id: uuid.UUID
    title: str | None = None
    user: UserResponse
    game: Game


class AdminModerationCommentItem(CommentBase, TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    moderation_status: ModerationStatus
    moderation_reason: str | None = None
    content_version: int
    moderated_version: int
    user: UserResponse
    review: AdminModerationCommentReviewSummary
    latest_moderation: CommentModerationHistoryItem | None = None
    is_appeal: bool = False


class AdminModerationCommentQueuePagination(Pagination):
    items: list[AdminModerationCommentItem]
