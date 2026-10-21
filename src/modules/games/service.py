import uuid

from fastapi import HTTPException, status

from src.modules.developers.service import DeveloperService
from src.modules.games.models import Game, GameCreate
from src.modules.games.repository import GameRepository
from src.modules.games.schemas import GamePagination, GameResponse
from src.modules.genres.service import GenreService
from src.modules.platforms.service import PlatformService
from src.modules.publisher.service import PublisherService
from src.modules.stores.service import StoreService
from src.schemas.rawg_responses import GameSearchPagination
from src.services.rawg.client import RawgService


class GameService:
    def __init__(
        self,
        repo: GameRepository,
        dev_service: DeveloperService,
        pub_service: PublisherService,
        store_service: StoreService,
        genre_service: GenreService,
        platform_service: PlatformService,
        rawg_service: RawgService,
    ) -> None:
        self.repo = repo
        self.dev_service = dev_service
        self.pub_service = pub_service
        self.store_service = store_service
        self.genre_service = genre_service
        self.platform_service = platform_service
        self.rawg_client = rawg_service

    async def search_games(
        self, game_title: str = "", page: int = 1, limit: int = 20
    ) -> GameSearchPagination:
        games = await self.rawg_client.search_games(game_title=game_title, page=page, limit=limit)
        if games is None:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error fetching games from external service",
            )

        return games

    async def get_game_detail(self, game_slug: str) -> GameResponse:
        game = await self.repo.get_by_slug(game_slug)
        if game:
            return game

        api_game = await self.rawg_client.get_game_details(game_slug)
        if not api_game:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

        # If RAWG redirected to a canonical slug or the game already exists by RAWG ID, reuse it
        game = await self.repo.get_by_slug(api_game.slug)
        if not game:
            game = await self.repo.get_by_rawg_id(api_game.rawg_id)
        if game:
            return game

        developers = [
            await self.dev_service.find_or_create(developer) for developer in api_game.developers
        ]
        publishers = [await self.pub_service.find_or_create(pub) for pub in api_game.publishers]
        stores = [await self.store_service.create_or_find(store) for store in api_game.stores]
        genres = [await self.genre_service.find_or_create(genre) for genre in api_game.genres]
        platforms = [
            await self.platform_service.find_or_create(platform) for platform in api_game.platforms
        ]

        new_game = await self.repo.create(
            GameCreate(
                title=api_game.title,
                slug=api_game.slug,
                rawg_id=api_game.rawg_id,
                description=api_game.description,
                metacritic_score=api_game.metacritic_score,
                metacritic_url=api_game.metacritic_url,
                website=api_game.website,
                release_date=api_game.release_date,
                image_url=api_game.image_url,
                background_image=api_game.background_image,
                screenshots=api_game.screenshots,
            ),
            developers=developers,
            publishers=publishers,
            stores=stores,
            genres=genres,
            platforms=platforms,
        )
        return new_game

    async def get_all(self, page: int, limit: int) -> GamePagination:
        offset = (page - 1) * limit
        games = await self.repo.get_all(offset, limit)
        total = await self.repo.count_all()
        total_pages = (total - 1 + limit) // limit if total > 0 else 0
        return GamePagination(
            items=games,
            total_pages=total_pages,
            page=page,
            total=total,
        )

    async def get_by_id(self, game_id: uuid.UUID) -> Game:
        game = await self.repo.get_by_id(game_id)
        if not game:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")

        return game
