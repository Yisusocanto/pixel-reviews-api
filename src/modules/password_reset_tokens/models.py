import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from pydantic.alias_generators import to_camel
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.modules.users.models import User


class PasswordResetTokenBase(SQLModel):
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        validate_by_alias=True,
        validate_by_name=True,
    )

    user_id: uuid.UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    token_hash: str
    expires_at: datetime = Field(sa_type=DateTime(timezone=True))


class PasswordResetToken(PasswordResetTokenBase, table=True):
    __tablename__ = "password_reset_token"

    id: uuid.UUID = Field(primary_key=True, default_factory=uuid.uuid4)

    user: "User" = Relationship(back_populates="password_reset_tokens")  # noqa: UP037


class PasswordResetTokenCreate(PasswordResetTokenBase):
    pass
