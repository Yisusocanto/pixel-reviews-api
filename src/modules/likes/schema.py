import uuid

from src.modules.likes.models import LikeBase
from src.schemas.config_base import ConfigBase


class LikeResponse(LikeBase):
    id: uuid.UUID
    user_id: uuid.UUID


class LikeToggleResponse(ConfigBase):
    liked: bool
    likes_count: int
