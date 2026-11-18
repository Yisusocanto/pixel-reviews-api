import uuid
from enum import StrEnum

from src.schemas.config_base import ConfigBase


class ModerationType(StrEnum):
    REVIEW = "review"


class ModerationPayload(ConfigBase):
    id: uuid.UUID
    version: int
    type: ModerationType
    title: str | None = None
    content: str | None = None
