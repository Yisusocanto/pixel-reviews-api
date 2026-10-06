import uuid

from src.core.mixins import TimestampMixin
from src.modules.comments.models import CommentBase
from src.modules.reviews.models import Review
from src.modules.users.models import UserResponse
from src.schemas.pagination import Pagination


class CommentResponse(CommentBase, TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID

    user: UserResponse
    review: Review


class CommentPagination(Pagination):
    items: list[CommentResponse]
