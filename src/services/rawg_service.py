import logging
from typing import Any

import httpx

from src.core.settings import settings
from src.developers.models import DeveloperCreate
from src.publisher.models import PublisherCreate
from src.schemas.rawg_responses import GameDetailRawgResponse, GameSearchRawgResponse

logger = logging.getLogger("rawg_service")

API_URL = "https://api.rawg.io/api"


class RawgService:
    async def _get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> httpx.Response | None:
        """Centralized HTTP GET request with logging and error reporting."""
        query_params: dict[str, Any] = {"key": settings.API_RAWG_KEY}
        if params:
            query_params.update(params)

        safe_params = {k: v for k, v in query_params.items() if k != "key"}
        logger.info("[RAWG] GET %s | Params: %s", endpoint, safe_params)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{API_URL}{endpoint}", params=query_params)

            if response.is_error:
                logger.error(
                    "[RAWG] Error on %s -> Status: %d | Body: %s",
                    endpoint,
                    response.status_code,
                    response.text,
                )
                return None

            logger.info("[RAWG] %s -> %d OK", endpoint, response.status_code)
            return response

        except httpx.RequestError as exc:
            logger.error("[RAWG] Connection error on %s: %s", endpoint, exc)
            return None
        except Exception:
            logger.exception("[RAWG] Unexpected error on %s", endpoint)
            return None

    async def search_games(
        self, game_title: str, limit: int
    ) -> list[GameSearchRawgResponse] | None:
        response = await self._get(
            "/games",
            params={"search": game_title, "page_size": limit},
        )
        if not response:
            return None

        games_json = response.json()
        results = games_json.get("results", [])

        games = [
            GameSearchRawgResponse(
                title=game.get("name", ""),
                slug=game.get("slug", ""),
                release_date=game.get("released"),
                background_image=game.get("background_image"),
            )
            for game in results
        ]

        logger.debug("[RAWG] search '%s' -> %d results", game_title, len(games))
        return games

    async def get_game_details(self, game_slug: str) -> GameDetailRawgResponse | None:
        response = await self._get(f"/games/{game_slug}")
        if not response:
            return None

        screenshots = await self.get_game_screenshots(game_slug)
        game_json = response.json()

        return GameDetailRawgResponse(
            rawg_id=game_json["id"],
            title=game_json.get("name") or game_json.get("title", ""),
            slug=game_json.get("slug", game_slug),
            description=game_json.get("description_raw", ""),
            release_date=game_json.get("released"),
            image_url=game_json.get("background_image"),
            screenshots=screenshots,
            developers=[
                DeveloperCreate(
                    rawg_id=developer.get("id"),
                    name=developer.get("name"),
                    slug=developer.get("slug"),
                )
                for developer in game_json.get("developers", [])
            ],
            publishers=[
                PublisherCreate(
                    rawg_id=pub.get("id"),
                    name=pub.get("name"),
                    slug=pub.get("slug"),
                )
                for pub in game_json.get("publishers", [])
            ],
        )

    async def get_game_screenshots(self, game_slug: str) -> list[str]:
        response = await self._get(f"/games/{game_slug}/screenshots")
        if not response:
            return []

        data = response.json()
        results = data.get("results", [])
        return [screenshot["image"] for screenshot in results if "image" in screenshot]


rawg_service = RawgService()
