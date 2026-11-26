import uuid
from collections.abc import Sequence

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.games.models import Game
from src.modules.genres.models import GameGenreLink, Genre, GenreCreate
from src.modules.stores.models import GameStoreLink


class GenreRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: GenreCreate) -> Genre:
        stmt = (
            pg_insert(Genre).values(**data.model_dump(), id=uuid.uuid7()).on_conflict_do_nothing()
        )
        await self.session.exec(stmt)
        result = await self.session.exec(
            select(Genre).where(Genre.slug == data.slug).execution_options(populate_existing=True)
        )
        return result.one()

    async def get_by_id(self, genre_id: uuid.UUID) -> Genre | None:
        return await self.session.get(Genre, genre_id)

    async def get_by_slug(self, slug: str) -> Genre | None:
        stmt = select(Genre).where(Genre.slug == slug)
        result = await self.session.exec(stmt)
        return result.first()

    async def list_all(self) -> Sequence[Genre]:
        stmt = select(Genre).order_by(col(Genre.name).asc())
        result = await self.session.exec(stmt)
        return result.all()

    async def list_games_by_genre(
        self, genre_id: uuid.UUID, offset: int, limit: int
    ) -> Sequence[Game]:
        stmt = (
            select(Game)
            .join(GameGenreLink, GameGenreLink.game_id == Game.id)
            .where(GameGenreLink.genre_id == genre_id)
            .options(
                selectinload(Game.developers),
                selectinload(Game.publishers),
                selectinload(Game.store_links).selectinload(GameStoreLink.store),
                selectinload(Game.genres),
                selectinload(Game.platforms),
            )
            .order_by(col(Game.critic_score).desc().nullslast(), col(Game.title).asc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.exec(stmt)
        return result.all()

    async def count_games_by_genre(self, genre_id: uuid.UUID) -> int:
        stmt = (
            select(func.count(col(Game.id)))
            .join(GameGenreLink, GameGenreLink.game_id == Game.id)
            .where(GameGenreLink.genre_id == genre_id)
        )
        result = await self.session.exec(stmt)
        total = result.first()
        return total if total is not None else 0
