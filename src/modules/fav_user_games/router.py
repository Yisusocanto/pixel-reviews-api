from fastapi import APIRouter

from src.modules.auth.dependencies import CurrentUserDep
from src.modules.fav_user_games.dependencies import FavUserGameServiceDep
from src.modules.fav_user_games.schemas import AddFavUserGamesRequest
from src.modules.games.models import Game

router = APIRouter(prefix="/favorites", tags=["Favorites User Games"])


@router.patch("", response_model=list[Game])
async def update_fav_user_games(
    service: FavUserGameServiceDep, data: AddFavUserGamesRequest, user: CurrentUserDep
):
    return await service.update_fav_user_games(data, user.id)
