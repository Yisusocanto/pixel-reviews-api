from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, Request

from src.modules.auth.dependencies import OptionalCurrentUserDep
from src.modules.games.dependencies import GameServiceDep
from src.modules.games.schemas import GamePagination, GameResponse, GameStats
from src.modules.games.translation import translate_and_persist_game_es
from src.modules.reviews.dependencies import ReviewServiceDep
from src.modules.reviews.schemas import ReviewPagination
from src.schemas.igdb_responses import GameSearchPagination
from src.services.gemini.dependencies import GeminiServiceDep

router = APIRouter(prefix="/games", tags=["Games"])


@router.get("", response_model=GamePagination)
async def get_all(
    service: GameServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
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
async def game_details(
    game_slug: str,
    request: Request,
    bg_tasks: BackgroundTasks,
    service: GameServiceDep,
    gemini: GeminiServiceDep,
    lang: Annotated[str, Query()] = "en",
):
    game = await service.get_game_detail(game_slug)
    if (
        lang.lower() == "es"
        and not game.description_es
        and game.description.strip()
        and gemini.api_key
    ):
        redis_client = getattr(request.app.state, "redis", None)
        bg_tasks.add_task(translate_and_persist_game_es, game.id, gemini, redis_client)
    return game


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
