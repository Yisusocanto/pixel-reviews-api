from fastapi import HTTPException, status

from src.modules.genres.models import Genre, GenreCreate
from src.modules.genres.repository import GenreRepository
from src.modules.genres.schemas import GenreGamesPagination


class GenreService:
    def __init__(self, repo: GenreRepository):
        self.repo = repo

    async def find_or_create(self, data: GenreCreate) -> Genre:
        existing_genre = await self.repo.get_by_slug(data.slug)
        if not existing_genre:
            new_genre = await self.repo.create(data)
            return new_genre

        return existing_genre

    async def list_all(self) -> list[Genre]:
        return list(await self.repo.list_all())

    async def get_games_by_slug(
        self, genre_slug: str, page: int = 1, limit: int = 24
    ) -> GenreGamesPagination:
        genre = await self.repo.get_by_slug(genre_slug)
        if not genre:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Genre not found",
            )
        offset = (page - 1) * limit
        games = await self.repo.list_games_by_genre(genre.id, offset=offset, limit=limit)
        total = await self.repo.count_games_by_genre(genre.id)
        total_pages = (total - 1 + limit) // limit if total > 0 else 0
        return GenreGamesPagination(
            genre=genre,
            items=list(games),
            page=page,
            total=total,
            total_pages=total_pages,
        )
