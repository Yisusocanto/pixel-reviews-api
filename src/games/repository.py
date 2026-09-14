from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.games.models import Game, GameCreate


class GameRepository:
    async def create(self, session: AsyncSession, data: GameCreate) -> Game:
        new_game = Game(**data.model_dump())
        session.add(new_game)
        await session.flush()
        await session.refresh(new_game)
        return new_game

    async def get_by_slug(self, session: AsyncSession, game_slug: str) -> Game | None:
        stmt = select(Game).where(Game.slug == game_slug)
        result = await session.exec(stmt)
        return result.first()

    async def get_by_id(self, session: AsyncSession, game_id: int) -> Game | None:
        game = await session.get(Game, game_id)
        return game

    async def get_all(self, session: AsyncSession, offset: int, limit: int):
        stmt = select(Game).offset(offset).limit(limit)
        result = await session.exec(stmt)
        return result.all()

    async def count_all(self, session: AsyncSession) -> int:
        stmt = select(func.count(Game.id))
        result = await session.exec(stmt)
        total = result.first()
        return total if total is not None else 0


game_repo = GameRepository()
