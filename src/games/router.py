from typing import Annotated

from fastapi import APIRouter, Query

from src.auth.dependencies import SessionDep
from src.games.schemas import GamePagination, GameResponse
from src.games.service import game_service
from src.schemas.rawg_responses import GameSearchRawgResponse

router = APIRouter(prefix="/games", tags=["Games"])


@router.get("", response_model=GamePagination)
async def get_all(
    session: SessionDep,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1)] = 10,
):
    return await game_service.get_all(session, page, limit)


@router.get("/search", response_model=list[GameSearchRawgResponse])
async def search_games(title: Annotated[str, Query()]):
    return await game_service.search_games(title)


@router.get("/{game_slug}", response_model=GameResponse)
async def game_details(game_slug: str, session: SessionDep):
    return await game_service.get_game_detail(session, game_slug)
