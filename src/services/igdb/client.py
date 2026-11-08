import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from src.modules.developers.models import DeveloperCreate
from src.modules.genres.models import GenreCreate
from src.modules.platforms.models import PlatformCreate
from src.modules.publisher.models import PublisherCreate
from src.modules.stores.models import StoreCreate
from src.schemas.igdb_responses import (
    GameDetailIgdbResponse,
    GameSearchIgdbResponse,
    GameSearchPagination,
)
from src.services.cache.client import CacheService

logger = logging.getLogger("igdb_service")

SEARCH_CACHE_TTL_SECONDS = 86400
TOKEN_CACHE_KEY = "igdb:oauth:access_token"
IGDB_IMAGE_BASE_URL = "https://images.igdb.com/igdb/image/upload"

KEY_ART_WITHOUT_LOGO_TYPE = 2
LANDSCAPE_ARTWORK_TYPES = {1, 2, 3, 4, 15}

STORE_RULES: list[tuple[tuple[str, ...], str, str, str]] = [
    (("store.steampowered.com", "steampowered.com"), "Steam", "steam", "store.steampowered.com"),
    (
        ("store.playstation.com", "playstation.com"),
        "PlayStation Store",
        "playstation-store",
        "store.playstation.com",
    ),
    (("xbox.com", "microsoft.com"), "Xbox Store", "xbox-store", "xbox.com"),
    (("nintendo.com",), "Nintendo eShop", "nintendo", "nintendo.com"),
    (("store.epicgames.com", "epicgames.com"), "Epic Games", "epic-games", "store.epicgames.com"),
    (("gog.com",), "GOG", "gog", "gog.com"),
    (("apps.apple.com", "itunes.apple.com"), "App Store", "apple-appstore", "apps.apple.com"),
    (("play.google.com",), "Google Play", "google-play", "play.google.com"),
    (("itch.io",), "itch.io", "itch", "itch.io"),
]

NON_OFFICIAL_DOMAINS = (
    "twitch.tv",
    "youtube.com",
    "youtu.be",
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "discord.gg",
    "discord.com",
    "reddit.com",
    "wikipedia.org",
    "fandom.com",
    "wiki.gg",
    "bsky.app",
    "tiktok.com",
)


def build_igdb_image_url(image_id: str | None, size: str = "t_1080p") -> str | None:
    if not image_id:
        return None
    return f"{IGDB_IMAGE_BASE_URL}/{size}/{image_id}.webp"


class IgdbService:
    _memory_token: str | None = None
    _memory_token_expires_at: float = 0.0

    def __init__(
        self,
        api_url: str,
        auth_url: str,
        client_id: str,
        client_secret: str,
        http_client: httpx.AsyncClient | None = None,
        cache: CacheService | None = None,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.auth_url = auth_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.http_client = http_client
        self.cache = cache or CacheService()

    async def _get_access_token(self, force_refresh: bool = False) -> str | None:
        if not force_refresh:
            cached_token = await self.cache.get(TOKEN_CACHE_KEY)
            if cached_token:
                return cached_token

            if (
                IgdbService._memory_token
                and time.monotonic() < IgdbService._memory_token_expires_at
            ):
                return IgdbService._memory_token

        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
        }

        try:
            if self.http_client is not None:
                response = await self.http_client.post(self.auth_url, params=params)
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(self.auth_url, params=params)

            if response.is_error:
                logger.error(
                    "[IGDB] OAuth token error -> Status: %d | Body: %s",
                    response.status_code,
                    response.text,
                )
                return None

            payload = response.json()
            token = payload.get("access_token")
            expires_in = int(payload.get("expires_in", 3600))
            if not token:
                return None

            ttl = max(60, expires_in - 300)
            IgdbService._memory_token = token
            IgdbService._memory_token_expires_at = time.monotonic() + ttl
            await self.cache.set(TOKEN_CACHE_KEY, token, ttl_seconds=ttl)
            return token

        except httpx.RequestError as exc:
            logger.error("[IGDB] OAuth connection error: %s", exc)
            return None
        except Exception:
            logger.exception("[IGDB] Unexpected error fetching OAuth token")
            return None

    async def _post(self, endpoint: str, body: str) -> Any | None:
        token = await self._get_access_token()
        if not token:
            return None

        url = f"{self.api_url}{endpoint}"
        headers = {
            "Client-ID": self.client_id,
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        try:
            if self.http_client is not None:
                response = await self.http_client.post(url, headers=headers, content=body)
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, headers=headers, content=body)

            if response.status_code == 401:
                refreshed_token = await self._get_access_token(force_refresh=True)
                if not refreshed_token:
                    return None
                headers["Authorization"] = f"Bearer {refreshed_token}"
                if self.http_client is not None:
                    response = await self.http_client.post(url, headers=headers, content=body)
                else:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(url, headers=headers, content=body)

            if response.is_error:
                logger.error(
                    "[IGDB] Error on %s -> Status: %d | Body: %s",
                    endpoint,
                    response.status_code,
                    response.text,
                )
                return None

            return response.json()

        except httpx.RequestError as exc:
            logger.error("[IGDB] Connection error on %s: %s", endpoint, exc)
            return None
        except Exception:
            logger.exception("[IGDB] Unexpected error on %s", endpoint)
            return None

    @staticmethod
    def _sanitize_query_term(term: str) -> str:
        return term.replace("\\", "").replace('"', "").strip()

    @staticmethod
    def _timestamp_to_datetime(ts: float | None) -> datetime | None:
        if ts is None:
            return None
        try:
            return datetime.fromtimestamp(ts, tz=UTC).replace(tzinfo=None)
        except OSError, OverflowError, ValueError:
            return None

    @staticmethod
    def _timestamp_to_date_str(ts: float | None) -> str | None:
        if ts is None:
            return None
        try:
            return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d")
        except OSError, OverflowError, ValueError:
            return None

    @staticmethod
    def _is_landscape_artwork(art: dict[str, Any]) -> bool:
        if not art.get("image_id"):
            return False
        art_type = art.get("artwork_type")
        if art_type is not None and art_type not in LANDSCAPE_ARTWORK_TYPES:
            return False
        width = art.get("width")
        height = art.get("height")
        return not (width and height and width <= height)

    @classmethod
    def _select_backdrop_id(
        cls,
        artworks: list[dict[str, Any]],
        screenshots: list[dict[str, Any]],
        cover_id: str | None,
    ) -> str | None:
        landscape_artworks = [a for a in artworks if cls._is_landscape_artwork(a)]

        for art in landscape_artworks:
            if art.get("artwork_type") == KEY_ART_WITHOUT_LOGO_TYPE:
                return art["image_id"]

        for shot in screenshots:
            if shot.get("image_id"):
                return shot["image_id"]

        if landscape_artworks:
            return landscape_artworks[0]["image_id"]

        return cover_id

    @staticmethod
    def _extract_websites_and_stores(
        websites: list[dict[str, Any]],
    ) -> tuple[str | None, list[StoreCreate]]:
        official_website: str | None = None
        stores_by_slug: dict[str, StoreCreate] = {}

        for item in websites:
            raw_url = (item.get("url") or "").strip()
            if not raw_url:
                continue

            parsed = urlparse(raw_url if "://" in raw_url else f"https://{raw_url}")
            host = parsed.netloc.lower().removeprefix("www.")
            if not host:
                continue

            matched_store = False
            for domains, store_name, store_slug, canonical_domain in STORE_RULES:
                if any(host == d or host.endswith(f".{d}") for d in domains):
                    matched_store = True
                    if store_slug not in stores_by_slug:
                        stores_by_slug[store_slug] = StoreCreate(
                            name=store_name,
                            slug=store_slug,
                            domain=canonical_domain,
                            url=raw_url,
                        )
                    break

            if matched_store:
                continue

            if official_website is None and not any(
                host == d or host.endswith(f".{d}") for d in NON_OFFICIAL_DOMAINS
            ):
                official_website = raw_url

        return official_website, list(stores_by_slug.values())

    @staticmethod
    def _extract_best_trailer(
        videos: list[dict[str, Any]],
    ) -> tuple[str | None, str | None]:
        valid_videos = [v for v in videos if v.get("video_id")]
        if not valid_videos:
            return None, None

        for keyword in ("launch trailer", "official trailer", "trailer", "gameplay"):
            for video in valid_videos:
                name = (video.get("name") or "").strip()
                if keyword in name.lower():
                    return video["video_id"], name or "Official Trailer"

        first = valid_videos[0]
        return first["video_id"], (first.get("name") or "Official Trailer").strip()

    async def search_games(
        self, game_title: str = "", page: int = 1, limit: int = 20
    ) -> GameSearchPagination | None:
        stripped = self._sanitize_query_term(game_title)
        cache_key = f"igdb:search:{stripped.lower()}:page:{page}:limit:{limit}"

        cached = await self.cache.get(cache_key)
        if cached is not None:
            logger.info("[IGDB] Cache HIT for '%s' (page %d)", stripped, page)
            return GameSearchPagination.model_validate_json(cached)

        offset = (page - 1) * limit
        fields = (
            "fields id, name, slug, first_release_date, aggregated_rating, total_rating, "
            "cover.image_id, artworks.image_id, artworks.artwork_type, artworks.width, artworks.height, "
            "screenshots.image_id;"
        )

        if stripped:
            items_query = (
                f'search "{stripped}"; {fields} '
                f"where version_parent = null; limit {limit}; offset {offset};"
            )
            count_query = f'search "{stripped}"; where version_parent = null;'
        else:
            where_clause = "where version_parent = null & cover != null & total_rating_count > 50;"
            items_query = (
                f"{fields} {where_clause} sort total_rating_count desc; "
                f"limit {limit}; offset {offset};"
            )
            count_query = where_clause

        items_data, count_data = await asyncio.gather(
            self._post("/games", items_query),
            self._post("/games/count", count_query),
        )

        if items_data is None:
            if page > 1:
                return GameSearchPagination(items=[], total=0, total_pages=0, page=page)
            return None

        total = (
            int(count_data.get("count", len(items_data)))
            if isinstance(count_data, dict)
            else len(items_data)
        )
        total_pages = (total - 1 + limit) // limit if total > 0 else 0

        games: list[GameSearchIgdbResponse] = []
        for game in items_data:
            cover_id = (game.get("cover") or {}).get("image_id")
            artworks = game.get("artworks") or []
            screenshots = game.get("screenshots") or []

            cover_url = build_igdb_image_url(cover_id, "t_cover_big_2x")
            backdrop_id = self._select_backdrop_id(artworks, screenshots, cover_id)
            backdrop_url = build_igdb_image_url(backdrop_id, "t_720p") or cover_url

            raw_rating = game.get("aggregated_rating") or game.get("total_rating")
            critic_score = round(raw_rating) if raw_rating is not None else None

            games.append(
                GameSearchIgdbResponse(
                    title=game.get("name", ""),
                    slug=game.get("slug", ""),
                    release_date=self._timestamp_to_date_str(game.get("first_release_date")),
                    image_url=cover_url or backdrop_url,
                    background_image=backdrop_url,
                    critic_score=critic_score,
                )
            )

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

    async def get_game_details(self, game_slug: str) -> GameDetailIgdbResponse | None:
        safe_slug = self._sanitize_query_term(game_slug)
        if not safe_slug:
            return None

        query = (
            "fields id, name, slug, summary, storyline, first_release_date, "
            "aggregated_rating, aggregated_rating_count, total_rating, total_rating_count, url, "
            "cover.image_id, artworks.image_id, artworks.artwork_type, artworks.width, artworks.height, "
            "screenshots.image_id, videos.name, videos.video_id, "
            "genres.name, genres.slug, platforms.name, platforms.slug, "
            "game_modes.name, themes.name, player_perspectives.name, "
            "involved_companies.developer, involved_companies.publisher, "
            "involved_companies.company.id, involved_companies.company.name, involved_companies.company.slug, "
            "websites.url; "
            f'where slug = "{safe_slug}"; '
            "limit 1;"
        )

        data = await self._post("/games", query)
        if not data or not isinstance(data, list):
            return None

        game_json = data[0]
        if "id" not in game_json:
            return None

        cover_id = (game_json.get("cover") or {}).get("image_id")
        artworks = game_json.get("artworks") or []
        raw_screenshots = game_json.get("screenshots") or []

        cover_url = build_igdb_image_url(cover_id, "t_cover_big_2x")
        primary_backdrop_id = self._select_backdrop_id(artworks, raw_screenshots, cover_id)
        background_image = build_igdb_image_url(primary_backdrop_id, "t_1080p")
        image_url = cover_url or background_image or ""

        landscape_artworks = [a for a in artworks if self._is_landscape_artwork(a)]
        gallery_urls: list[str] = []
        for item in [*raw_screenshots, *landscape_artworks]:
            img_url = build_igdb_image_url(item.get("image_id"), "t_1080p")
            if img_url and img_url not in gallery_urls:
                gallery_urls.append(img_url)

        developers: list[DeveloperCreate] = []
        publishers: list[PublisherCreate] = []
        seen_devs: set[int] = set()
        seen_pubs: set[int] = set()

        for inv in game_json.get("involved_companies") or []:
            company = inv.get("company") or {}
            comp_id = company.get("id")
            comp_name = company.get("name")
            comp_slug = company.get("slug")
            if not comp_id or not comp_name or not comp_slug:
                continue

            if inv.get("developer") and comp_id not in seen_devs:
                seen_devs.add(comp_id)
                developers.append(DeveloperCreate(igdb_id=comp_id, name=comp_name, slug=comp_slug))
            if inv.get("publisher") and comp_id not in seen_pubs:
                seen_pubs.add(comp_id)
                publishers.append(PublisherCreate(igdb_id=comp_id, name=comp_name, slug=comp_slug))

        website, stores = self._extract_websites_and_stores(game_json.get("websites") or [])
        trailer_id, trailer_title = self._extract_best_trailer(game_json.get("videos") or [])

        raw_critic = game_json.get("aggregated_rating")
        raw_critic_count = game_json.get("aggregated_rating_count")
        if raw_critic is None and game_json.get("total_rating") is not None:
            raw_critic = game_json.get("total_rating")
            raw_critic_count = game_json.get("total_rating_count")

        critic_score = round(raw_critic) if raw_critic is not None else None
        critic_score_count = int(raw_critic_count) if raw_critic_count is not None else None

        summary = (game_json.get("summary") or "").strip()
        storyline = (game_json.get("storyline") or "").strip() or None

        return GameDetailIgdbResponse(
            igdb_id=game_json["id"],
            title=game_json.get("name") or "",
            slug=game_json.get("slug") or safe_slug,
            description=summary or (storyline or ""),
            storyline=storyline if summary else None,
            critic_score=critic_score,
            critic_score_count=critic_score_count,
            igdb_url=game_json.get("url"),
            website=website,
            release_date=self._timestamp_to_datetime(game_json.get("first_release_date")),
            image_url=image_url,
            background_image=background_image,
            trailer_youtube_id=trailer_id,
            trailer_title=trailer_title,
            screenshots=gallery_urls,
            game_modes=[m["name"] for m in (game_json.get("game_modes") or []) if m.get("name")],
            themes=[t["name"] for t in (game_json.get("themes") or []) if t.get("name")],
            player_perspectives=[
                p["name"] for p in (game_json.get("player_perspectives") or []) if p.get("name")
            ],
            developers=developers,
            publishers=publishers,
            stores=stores,
            genres=[
                GenreCreate(name=g["name"], slug=g["slug"])
                for g in (game_json.get("genres") or [])
                if g.get("name") and g.get("slug")
            ],
            platforms=[
                PlatformCreate(name=p["name"], slug=p["slug"])
                for p in (game_json.get("platforms") or [])
                if p.get("name") and p.get("slug")
            ],
        )
