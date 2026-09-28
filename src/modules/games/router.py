from typing import Annotated

from fastapi import APIRouter, Query

from src.modules.games.dependencies import GameServiceDep
from src.modules.games.schemas import GamePagination, GameResponse
from src.modules.reviews.schemas import ReviewPagination
from src.schemas.rawg_responses import GameSearchRawgResponse

router = APIRouter(prefix="/games", tags=["Games"])


@router.get("", response_model=GamePagination)
async def get_all(
    service: GameServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await service.get_all(page, limit)


@router.get("/search", response_model=list[GameSearchRawgResponse])
async def search_games(title: Annotated[str, Query()], service: GameServiceDep):
    return await service.search_games(title)


@router.get("/{game_slug}", response_model=GameResponse)
async def game_details(game_slug: str, service: GameServiceDep):
    return await service.get_game_detail(game_slug)


@router.get("/{game_slug}/reviews", response_model=ReviewPagination)
async def get_game_reviews(
    service: GameServiceDep,
    game_slug: str,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await service.get_game_reviews(page, limit, game_slug)
