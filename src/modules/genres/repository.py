import uuid

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.modules.genres.models import Genre, GenreCreate


class GenreRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: GenreCreate) -> Genre:
        stmt = (
            pg_insert(Genre).values(**data.model_dump(), id=uuid.uuid4()).on_conflict_do_nothing()
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
