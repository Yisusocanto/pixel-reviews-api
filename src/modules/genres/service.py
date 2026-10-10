from src.modules.genres.models import Genre, GenreCreate
from src.modules.genres.repository import GenreRepository


class GenreService:
    def __init__(self, repo: GenreRepository):
        self.repo = repo

    async def find_or_create(self, data: GenreCreate) -> Genre:
        existing_genre = await self.repo.get_by_slug(data.slug)
        if not existing_genre:
            new_genre = await self.repo.create(data)
            return new_genre

        return existing_genre
