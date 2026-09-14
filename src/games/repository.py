from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.developers.models import Developer
from src.games.models import Game, GameCreate
from src.publisher.models import Publisher


class GameRepository:
    async def create(
        self,
        session: AsyncSession,
        data: GameCreate,
        developers: list[Developer],
        publishers: list[Publisher],
    ) -> Game:
        new_game = Game(**data.model_dump(), developers=developers, publishers=publishers)
        session.add(new_game)
        await session.flush()
        created_game = await self.get_by_slug(session, new_game.slug)
        return created_game or new_game

    async def get_by_slug(self, session: AsyncSession, game_slug: str) -> Game | None:
        stmt = (
            select(Game)
            .where(Game.slug == game_slug)
            .options(selectinload(Game.developers), selectinload(Game.publishers))
        )
        result = await session.exec(stmt)
        return result.first()

    async def get_by_id(self, session: AsyncSession, game_id: int) -> Game | None:
        game = await session.get(Game, game_id)
        return game

    async def get_all(self, session: AsyncSession, offset: int, limit: int):
        stmt = (
            select(Game)
            .offset(offset)
            .limit(limit)
            .options(selectinload(Game.developers), selectinload(Game.publishers))
        )
        result = await session.exec(stmt)
        return result.all()

    async def count_all(self, session: AsyncSession) -> int:
        stmt = select(func.count(Game.id))
        result = await session.exec(stmt)
        total = result.first()
        return total if total is not None else 0


game_repo = GameRepository()
