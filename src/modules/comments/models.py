import uuid
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlmodel import Field, Relationship, SQLModel

from src.core.mixins import TimestampMixin
from src.schemas.config_base import ConfigBase

if TYPE_CHECKING:
    from src.modules.reviews.models import Review
    from src.modules.users.models import User


class CommentBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    review_id: uuid.UUID = Field(foreign_key="review.id", index=True, ondelete="CASCADE")
    content: str


class Comment(CommentBase, TimestampMixin, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, ondelete="CASCADE")

    user: "User" = Relationship(back_populates="comments")  # noqa: UP037
    review: "Review" = Relationship(back_populates="comments")  # noqa: UP037


class CommentCreate(CommentBase):
    pass


class CommentUpdate(ConfigBase):
    content: str | None = None
