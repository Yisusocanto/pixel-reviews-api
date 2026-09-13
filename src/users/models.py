import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel

from src.lib.dates import get_current_date


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    bio: str | None = Field(default=None)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=get_current_date)
    updated_at: datetime = Field(default_factory=get_current_date)


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
