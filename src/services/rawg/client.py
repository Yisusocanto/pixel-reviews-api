import logging
from typing import Any

import httpx

from src.modules.developers.models import DeveloperCreate
from src.modules.genres.models import GenreCreate
from src.modules.platforms.models import PlatformCreate
from src.modules.publisher.models import PublisherCreate
from src.modules.stores.models import StoreCreate
from src.schemas.rawg_responses import (
    GameDetailRawgResponse,
    GameSearchPagination,
    GameSearchRawgResponse,
)
from src.services.cache.client import CacheService

logger = logging.getLogger("rawg_service")

SEARCH_CACHE_TTL_SECONDS = 86400


class RawgService:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        http_client: httpx.AsyncClient | None = None,
        cache: CacheService | None = None,
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.http_client = http_client
        self.cache = cache or CacheService()

    async def _get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> httpx.Response | None:
        """Centralized HTTP GET request with logging and error reporting."""
        query_params: dict[str, Any] = {"key": self.api_key}
        if params:
            query_params.update(params)

        safe_params = {k: v for k, v in query_params.items() if k != "key"}
        logger.info("[RAWG] GET %s | Params: %s", endpoint, safe_params)

        try:
            url = f"{self.api_url}{endpoint}"
            if self.http_client is not None:
                response = await self.http_client.get(url, params=query_params)
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(url, params=query_params)

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
        self, game_title: str = "", page: int = 1, limit: int = 20
    ) -> GameSearchPagination | None:
        stripped = game_title.strip()
        cache_key = f"rawg:search:{stripped.lower()}:page:{page}:limit:{limit}"

        cached = await self.cache.get(cache_key)
        if cached is not None:
            logger.info("[RAWG] Cache HIT for '%s' (page %d)", stripped, page)
            return GameSearchPagination.model_validate_json(cached)

        params: dict[str, Any] = {
            "page": page,
            "page_size": limit,
        }
        if stripped:
            params["search"] = stripped

        response = await self._get(
            "/games",
            params=params,
        )
        if not response:
            if page > 1:
                return GameSearchPagination(items=[], total=0, total_pages=0, page=page)
            return None

        games_json = response.json()
        results = games_json.get("results", [])
        total = games_json.get("count", 0)
        total_pages = (total - 1 + limit) // limit if total > 0 else 0

        games = [
            GameSearchRawgResponse(
                title=game.get("name", ""),
                slug=game.get("slug", ""),
                release_date=game.get("released"),
                background_image=game.get("background_image"),
            )
            for game in results
        ]

        result = GameSearchPagination(
            items=games,
            total=total,
            total_pages=total_pages,
            page=page,
        )
        await self.cache.set(
            cache_key, result.model_dump_json(), ttl_seconds=SEARCH_CACHE_TTL_SECONDS
        )
        return result

    async def get_game_details(self, game_slug: str) -> GameDetailRawgResponse | None:
        response = await self._get(f"/games/{game_slug}")
        if not response:
            return None

        game_json = response.json()

        # Handle RAWG slug redirects (e.g. {'redirect': True, 'slug': 'god-of-war-2'})
        if game_json.get("redirect") and game_json.get("slug"):
            redirect_slug = game_json["slug"]
            logger.info("[RAWG] Slug '%s' redirects to '%s'", game_slug, redirect_slug)
            return await self.get_game_details(redirect_slug)

        if "id" not in game_json:
            logger.error("[RAWG] Missing 'id' in game response for '%s': %s", game_slug, game_json)
            return None

        canonical_slug = game_json.get("slug", game_slug)
        screenshots = await self.get_game_screenshots(canonical_slug)

        return GameDetailRawgResponse(
            rawg_id=game_json["id"],
            title=game_json.get("name") or game_json.get("title", ""),
            slug=canonical_slug,
            description=game_json.get("description_raw", ""),
            metacritic_score=game_json.get("metacritic", None),
            metacritic_url=game_json.get("metacritic_url", None),
            website=game_json.get("website", None),
            release_date=game_json.get("released"),
            image_url=game_json.get("background_image"),
            background_image=game_json.get("background_image_additional"),
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
            stores=[
                StoreCreate(
                    name=store["store"]["name"],
                    slug=store["store"]["slug"],
                    domain=store["store"]["domain"],
                    url=store.get("url", None),
                )
                for store in game_json.get("stores", [])
            ],
            genres=[
                GenreCreate(
                    name=genre.get("name"),
                    slug=genre.get("slug"),
                )
                for genre in game_json.get("genres", [])
            ],
            platforms=[
                PlatformCreate(
                    slug=platform.get("platform", {}).get("slug"),
                    name=platform.get("platform", {}).get("name"),
                )
                for platform in game_json.get("platforms", [])
            ],
        )

    async def get_game_screenshots(self, game_slug: str) -> list[str]:
        response = await self._get(f"/games/{game_slug}/screenshots")
        if not response:
            return []

        data = response.json()
        results = data.get("results", [])
        return [screenshot["image"] for screenshot in results if "image" in screenshot]
