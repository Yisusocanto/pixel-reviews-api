import uuid
from collections.abc import Sequence

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload
from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.games.models import Game
from src.modules.platforms.models import GamePlatformLink, Platform, PlatformCreate
from src.modules.stores.models import GameStoreLink


class PlatformRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: PlatformCreate) -> Platform:
        stmt = (
            pg_insert(Platform)
            .values(**data.model_dump(), id=uuid.uuid7())
            .on_conflict_do_nothing()
        )
        await self.session.exec(stmt)
        result = await self.session.exec(
            select(Platform)
            .where(Platform.slug == data.slug)
            .execution_options(populate_existing=True)
        )
        return result.one()

    async def get_by_id(self, platform_id: uuid.UUID) -> Platform | None:
        return await self.session.get(Platform, platform_id)

    async def get_by_slug(self, slug: str) -> Platform | None:
        stmt = select(Platform).where(Platform.slug == slug)
        result = await self.session.exec(stmt)
        return result.first()

    async def list_all(self) -> Sequence[Platform]:
        stmt = select(Platform).order_by(col(Platform.name).asc())
        result = await self.session.exec(stmt)
        return result.all()

    async def list_games_by_platform(
        self, platform_id: uuid.UUID, offset: int, limit: int
    ) -> Sequence[Game]:
        stmt = (
            select(Game)
            .join(GamePlatformLink, GamePlatformLink.game_id == Game.id)
            .where(GamePlatformLink.platform_id == platform_id)
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

    async def count_games_by_platform(self, platform_id: uuid.UUID) -> int:
        stmt = (
            select(func.count(col(Game.id)))
            .join(GamePlatformLink, GamePlatformLink.game_id == Game.id)
            .where(GamePlatformLink.platform_id == platform_id)
        )
        result = await self.session.exec(stmt)
        total = result.first()
        return total if total is not None else 0
