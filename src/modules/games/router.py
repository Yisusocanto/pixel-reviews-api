from typing import Annotated

from fastapi import APIRouter, Query

from src.modules.auth.dependencies import OptionalCurrentUserDep
from src.modules.games.dependencies import GameServiceDep
from src.modules.games.schemas import GamePagination, GameResponse, GameStats
from src.modules.reviews.dependencies import ReviewServiceDep
from src.modules.reviews.schemas import ReviewPagination
from src.schemas.rawg_responses import GameSearchPagination

router = APIRouter(prefix="/games", tags=["Games"])


@router.get("", response_model=GamePagination)
async def get_all(
    service: GameServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await service.get_all(page, limit)


@router.get("/search", response_model=GameSearchPagination)
async def search_games(
    service: GameServiceDep,
    title: Annotated[str, Query()] = "",
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    return await service.search_games(game_title=title, page=page, limit=limit)


@router.get("/{game_slug}", response_model=GameResponse)
async def game_details(game_slug: str, service: GameServiceDep):
    return await service.get_game_detail(game_slug)


@router.get("/{game_slug}/reviews", response_model=ReviewPagination)
async def get_game_reviews(
    game_slug: str,
    game_service: GameServiceDep,
    review_service: ReviewServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
    current_user: OptionalCurrentUserDep = None,
):
    game = await game_service.get_game_detail(game_slug)
    current_user_id = current_user.id if current_user else None
    return await review_service.get_all(
        page=page, limit=limit, game_id=game.id, current_user_id=current_user_id
    )


@router.get("/{game_slug}/stats", response_model=GameStats)
async def game_stats(service: GameServiceDep, review_service: ReviewServiceDep, game_slug: str):
    game = await service.get_game_detail(game_slug)
    return await review_service.game_stats(game.id)
