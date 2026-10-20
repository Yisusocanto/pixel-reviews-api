import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import ConfigDict, computed_field
from pydantic.alias_generators import to_camel
from sqlmodel import Field, Relationship, SQLModel

from src.core.mixins import TimestampMixin
from src.core.settings import settings
from src.modules.password_reset_tokens.models import PasswordResetToken
from src.schemas.config_base import ConfigBase

if TYPE_CHECKING:
    from src.modules.comments.models import Comment
    from src.modules.likes.models import Like
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
    bio: str | None = Field(default=None, max_length=1000)


class User(UserBase, TimestampMixin, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str | None = Field(default=None, nullable=True)
    google_id: str | None = Field(default=None, unique=True, index=True)
    profile_photo_key: str | None = Field(default=None)

    reviews: list["Review"] = Relationship(  # noqa: UP037
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    wishlist: list["Wishlist"] = Relationship(  # noqa: UP037
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    likes: list["Like"] = Relationship(  # noqa: UP037
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    comments: list["Comment"] = Relationship(  # noqa: UP037
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    password_reset_tokens: "PasswordResetToken" = Relationship(  # noqa: UP037
        back_populates="user", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    profile_photo_key: str | None = Field(default=None, exclude=True)
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def profile_photo_url(self) -> str | None:
        if not self.profile_photo_key:
            return None
        return f"{settings.CF_PUBLIC_URL.rstrip('/')}/{self.profile_photo_key}"


class UserUpdate(ConfigBase):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    bio: str | None = Field(default=None, max_length=1000)
