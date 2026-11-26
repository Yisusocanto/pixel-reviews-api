from typing import Annotated

from fastapi import APIRouter, Query

from src.modules.genres.dependencies import GenreServiceDep
from src.modules.genres.models import Genre
from src.modules.genres.schemas import GenreGamesPagination

router = APIRouter(prefix="/genres", tags=["Genres"])


@router.get("", response_model=list[Genre])
async def list_genres(service: GenreServiceDep):
    return await service.list_all()


@router.get("/{genre_slug}/games", response_model=GenreGamesPagination)
async def list_genre_games(
    genre_slug: str,
    service: GenreServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=50)] = 24,
):
    return await service.get_games_by_slug(genre_slug=genre_slug, page=page, limit=limit)
