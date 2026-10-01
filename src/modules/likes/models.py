import uuid
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from src.core.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.modules.reviews.models import Review
    from src.modules.users.models import User


class LikeBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    review_id: uuid.UUID = Field(foreign_key="review.id", ondelete="CASCADE")


class Like(LikeBase, TimestampMixin, table=True):
    __tablename__ = "likes"

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")

    user: "User" = Relationship(back_populates="likes")  # noqa: UP037
    review: "Review" = Relationship(back_populates="likes")  # noqa: UP037

    __table_args__ = (UniqueConstraint("review_id", "user_id", name="uq_review_user"),)


class LikeCreate(LikeBase):
    pass
