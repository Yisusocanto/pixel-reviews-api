import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.developers.models import Developer, GameDeveloperLink
from src.modules.games.models import Game, GameCreate
from src.modules.genres.models import GameGenreLink, Genre
from src.modules.platforms.models import GamePlatformLink, Platform
from src.modules.publisher.models import GamePublisherLink, Publisher
from src.modules.stores.models import GameStoreLink, Store


class GameRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        data: GameCreate,
        developers: list[Developer],
        publishers: list[Publisher],
        stores: list[Store],
        genres: list[Genre],
        platforms: list[Platform],
    ) -> Game:
        # Atomic upsert: if a concurrent request already inserted this game, do nothing.
        game_id = uuid.uuid4()
        await self.session.exec(
            pg_insert(Game).values(**data.model_dump(), id=game_id).on_conflict_do_nothing()
        )
        game = await self.get_by_rawg_id(data.rawg_id)
        if game is None:
            raise RuntimeError("Game was not found after upsert")

        # Only the request that actually inserted the game links its developers/publishers/stores.
        if game.id == game_id:
            if developers:
                await self.session.exec(
                    pg_insert(GameDeveloperLink)
                    .values([{"game_id": game_id, "developer_id": d.id} for d in developers])
                    .on_conflict_do_nothing()
                )
            if publishers:
                await self.session.exec(
                    pg_insert(GamePublisherLink)
                    .values([{"game_id": game_id, "publisher_id": p.id} for p in publishers])
                    .on_conflict_do_nothing()
                )
            if stores:
                await self.session.exec(
                    pg_insert(GameStoreLink).values(
                        [{"game_id": game_id, "store_id": s.id} for s in stores]
                    )
                )
            if genres:
                await self.session.exec(
                    pg_insert(GameGenreLink).values(
                        [{"game_id": game_id, "genre_id": g.id} for g in genres]
                    )
                )
            if platforms:
                await self.session.exec(
                    pg_insert(GamePlatformLink).values(
                        [{"game_id": game_id, "platform_id": p.id} for p in platforms]
                    )
                )

            await self.session.refresh(game, ["developers", "publishers", "stores"])
        return game

    async def get_by_slug(self, game_slug: str) -> Game | None:
        stmt = (
            select(Game)
            .where(Game.slug == game_slug)
            .options(
                selectinload(Game.developers),
                selectinload(Game.publishers),
                selectinload(Game.stores),
                selectinload(Game.genres),
                selectinload(Game.platforms),
            )
        )
        result = await self.session.exec(stmt)
        return result.first()

    async def get_by_rawg_id(self, rawg_id: int) -> Game | None:
        stmt = (
            select(Game)
            .where(Game.rawg_id == rawg_id)
            .options(
                selectinload(Game.developers),
                selectinload(Game.publishers),
                selectinload(Game.stores),
                selectinload(Game.genres),
                selectinload(Game.platforms),
            )
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
            .options(
                selectinload(Game.developers),
                selectinload(Game.publishers),
                selectinload(Game.stores),
                selectinload(Game.genres),
                selectinload(Game.platforms),
            )
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def count_all(self) -> int:
        stmt = select(func.count(Game.id))
        result = await self.session.exec(stmt)
        total = result.first()
        return total if total is not None else 0
