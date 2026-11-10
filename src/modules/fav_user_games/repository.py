import uuid

from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.fav_user_games.models import FavUserGame
from src.modules.games.models import Game


class FavUserGameRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_games(self, games: list[FavUserGame]):
        self.session.add_all(games)
        await self.session.flush()
        return games

    async def remove(self, user_id: uuid.UUID) -> int:
        stmt = delete(FavUserGame).where(FavUserGame.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.rowcount

    async def get_all(self, user_id: uuid.UUID) -> list[Game]:
        stmt = select(Game).join(FavUserGame).where(FavUserGame.user_id == user_id)
        result = await self.session.exec(stmt)
        return result.all()
