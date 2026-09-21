import uuid

from src.core.mixins import TimestampMixin
from src.modules.games.models import Game
from src.modules.users.models import UserResponse
from src.modules.wishlists.models import WishlistBase
from src.schemas.pagination import Pagination


class WishlistResponse(WishlistBase, TimestampMixin):
    id: uuid.UUID
    user: UserResponse
    game: Game


class WishlistPagination(Pagination):
    items: list[WishlistResponse]
