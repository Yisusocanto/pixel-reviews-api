import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.modules.games.models import Game


class GamePublisherLink(SQLModel, table=True):
    game_id: uuid.UUID = Field(primary_key=True, foreign_key="game.id")
    publisher_id: uuid.UUID = Field(primary_key=True, foreign_key="publisher.id")


class PublisherBase(SQLModel):
    rawg_id: int = Field(index=True, unique=True)
    slug: str = Field(index=True, unique=True)
    name: str = Field(index=True)


class Publisher(PublisherBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    games: list["Game"] = Relationship(back_populates="publishers", link_model=GamePublisherLink)  # noqa: UP037


class PublisherCreate(PublisherBase):
    pass
