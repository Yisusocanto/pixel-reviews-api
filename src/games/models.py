import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Column, String
from sqlmodel import Field, SQLModel


class GameBase(SQLModel):
    title: str = Field(index=True)
    slug: str = Field(index=True, unique=True)
    rawg_id: int = Field(index=True, unique=True)
    release_date: datetime
    image_url: str
    description: str
    screenshots: list[str] = Field(
        default_factory=list, sa_column=Column(ARRAY(String), nullable=False, server_default="{}")
    )


class Game(GameBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class GameCreate(GameBase):
    pass
