from fastapi import HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession

from src.developers.service import developer_service
from src.games.models import GameCreate
from src.games.repository import game_repo
from src.games.schemas import GamePagination, GameResponse
from src.publisher.service import publisher_service
from src.schemas.rawg_responses import GameSearchRawgResponse
from src.services.rawg_service import rawg_service


class GameService:
    async def search_games(self, game_title) -> list[GameSearchRawgResponse]:
        games = await rawg_service.search_games(game_title, 20)
        if not games:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Games not found")

        return games

    async def get_game_detail(self, session: AsyncSession, game_slug: str) -> GameResponse:
        game = await game_repo.get_by_slug(session, game_slug)
        if game:
            return game

        api_game = await rawg_service.get_game_details(game_slug)
        if not api_game:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

        developers = [
            await developer_service.find_or_create(session, developer)
            for developer in api_game.developers
        ]
        publishers = [
            await publisher_service.find_or_create(session, pub) for pub in api_game.publishers
        ]

        new_game = await game_repo.create(
            session,
            GameCreate(
                title=api_game.title,
                slug=api_game.slug,
                rawg_id=api_game.rawg_id,
                description=api_game.description,
                release_date=api_game.release_date,
                image_url=api_game.image_url,
                screenshots=api_game.screenshots,
            ),
            developers=developers,
            publishers=publishers,
        )
        return new_game

    async def get_all(self, session: AsyncSession, page: int, limit: int) -> GamePagination:
        offset = (page - 1) * limit
        games = await game_repo.get_all(session, offset, limit)
        total = await game_repo.count_all(session)
        total_pages = (total - 1 + limit) // limit if total > 0 else 0
        return GamePagination(
            items=games,
            total_pages=total_pages,
            page=page,
            total=total,
        )


game_service = GameService()
