from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.genres.repository import GenreRepository
from src.modules.genres.service import GenreService


def get_genre_repository(session: SessionDep) -> GenreRepository:
    return GenreRepository(session)


GenreRepositoryDep = Annotated[GenreRepository, Depends(get_genre_repository)]


def get_genre_service(repo: GenreRepositoryDep) -> GenreService:
    return GenreService(repo)


GenreServiceDep = Annotated[GenreService, Depends(get_genre_service)]
