import uuid

from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.developers.models import Developer
from src.modules.games.models import Game, GameCreate
from src.modules.publisher.models import Publisher


class GameRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        data: GameCreate,
        developers: list[Developer],
        publishers: list[Publisher],
    ) -> Game:
        new_game = Game(**data.model_dump(), developers=developers, publishers=publishers)
        self.session.add(new_game)
        await self.session.flush()
        created_game = await self.get_by_slug(new_game.slug)
        return created_game or new_game

    async def get_by_slug(self, game_slug: str) -> Game | None:
        stmt = (
            select(Game)
            .where(Game.slug == game_slug)
            .options(selectinload(Game.developers), selectinload(Game.publishers))
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_by_rawg_id(self, rawg_id: int) -> Game | None:
        stmt = (
            select(Game)
            .where(Game.rawg_id == rawg_id)
            .options(selectinload(Game.developers), selectinload(Game.publishers))
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_by_id(self, game_id: uuid.UUID) -> Game | None:
        game = await self.session.get(Game, game_id)
        return game

    async def get_all(self, offset: int, limit: int):
        stmt = (
            select(Game)
            .offset(offset)
            .limit(limit)
            .options(selectinload(Game.developers), selectinload(Game.publishers))
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def count_all(self) -> int:
        stmt = select(func.count(Game.id))
        result = await self.session.exec(stmt)
        total = result.first()
        return total if total is not None else 0
