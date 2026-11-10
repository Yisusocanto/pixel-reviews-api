from typing import Annotated

from fastapi import Depends

from src.modules.auth.dependencies import SessionDep
from src.modules.fav_user_games.repository import FavUserGameRepository
from src.modules.fav_user_games.service import FavUserGameService
from src.modules.games.dependencies import GameServiceDep


def get_fav_user_game_repository(session: SessionDep) -> FavUserGameRepository:
    return FavUserGameRepository(session)


FavUserGameRepositoryDep = Annotated[FavUserGameRepository, Depends(get_fav_user_game_repository)]


def get_fav_user_game_service(
    repo: FavUserGameRepositoryDep, game_service: GameServiceDep
) -> FavUserGameService:
    return FavUserGameService(repo=repo, game_service=game_service)


FavUserGameServiceDep = Annotated[FavUserGameService, Depends(get_fav_user_game_service)]
