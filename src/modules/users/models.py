import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlmodel import Field, Relationship, SQLModel

from src.core.mixins import TimestampMixin

if TYPE_CHECKING:
    from src.modules.reviews.models import Review
    from src.modules.wishlists.models import Wishlist


class UserBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    bio: str | None = Field(default=None)


class User(UserBase, TimestampMixin, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(nullable=False)

    reviews: list["Review"] = Relationship(  # noqa: UP037
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    wishlist: list["Wishlist"] = Relationship(  # noqa: UP037
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
