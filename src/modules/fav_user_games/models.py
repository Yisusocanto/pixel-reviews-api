import uuid

from sqlmodel import Field, SQLModel


class FavUserGame(SQLModel, table=True):
    __tablename__ = "fav_user_games"

    game_id: uuid.UUID = Field(primary_key=True, foreign_key="game.id", ondelete="CASCADE")
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="users.id", ondelete="CASCADE")
