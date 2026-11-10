import uuid

from fastapi import HTTPException

from src.modules.fav_user_games.models import FavUserGame
from src.modules.fav_user_games.repository import FavUserGameRepository
from src.modules.fav_user_games.schemas import AddFavUserGamesRequest
from src.modules.games.models import Game
from src.modules.games.service import GameService


class FavUserGameService:
    def __init__(self, repo: FavUserGameRepository, game_service: GameService):
        self.repo = repo
        self.game_service = game_service

    async def update_fav_user_games(self, data: AddFavUserGamesRequest, user_id: uuid.UUID):
        if len(data.games_slugs) != len(set(data.games_slugs)):
            raise HTTPException(status_code=400, detail="Slugs must unique")

        if len(data.games_slugs) < 1:
            await self.repo.remove(user_id)
            return []

        games = [await self.game_service.get_game_detail(slug) for slug in data.games_slugs]
        fav_games = [FavUserGame(game_id=game.id, user_id=user_id) for game in games]

        await self.repo.remove(user_id)
        await self.repo.add_games(fav_games)
        return games

    async def get_all(self, user_id: uuid.UUID) -> list[Game]:
        games = await self.repo.get_all(user_id)
        return games
