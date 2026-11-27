import logging
import uuid
from datetime import UTC, datetime

from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.core.settings import settings
from src.db.database import async_session_maker
from src.modules.games.models import Game
from src.services.gemini.client import GeminiService

logger = logging.getLogger("game_translation")


async def _consume_translation_budget(redis_client: Redis | None) -> bool:
    if redis_client is None:
        return True
    now = datetime.now(UTC)
    minute_key = f"quota:translate:minute:{now.strftime('%Y%m%d%H%M')}"
    daily_key = f"quota:translate:daily:{now.strftime('%Y%m%d')}"
    try:
        minute_count = await redis_client.incr(minute_key)
        if minute_count == 1:
            await redis_client.expire(minute_key, 90)
        if minute_count > settings.GEMINI_TRANSLATION_PER_MINUTE_LIMIT:
            logger.info("[TRANSLATE] Skipped: per-minute translation budget reached")
            return False

        daily_count = await redis_client.incr(daily_key)
        if daily_count == 1:
            await redis_client.expire(daily_key, 90000)
        if daily_count > settings.GEMINI_TRANSLATION_DAILY_LIMIT:
            logger.info("[TRANSLATE] Skipped: daily translation budget reached")
            return False
    except RedisError:
        logger.warning("[TRANSLATE] Redis budget counter unavailable; proceeding cautiously")
    return True


async def translate_and_persist_game_es(
    game_id: uuid.UUID,
    gemini: GeminiService,
    redis_client: Redis | None = None,
) -> None:
    lock_key = f"lock:translate:game:{game_id}"
    if redis_client is not None:
        try:
            acquired = await redis_client.set(lock_key, "1", ex=300, nx=True)
            if not acquired:
                return
        except RedisError:
            logger.warning("[TRANSLATE] Redis lock unavailable for game %s", game_id)

    try:
        async with async_session_maker() as session:
            game = await session.get(Game, game_id)
            if not game or game.description_es or not game.description.strip():
                return

            if not await _consume_translation_budget(redis_client):
                return

            translated = await gemini.translate_game_copy_to_spanish(
                title=game.title,
                description=game.description,
                storyline=game.storyline,
            )
            if translated.get("description_es"):
                game.description_es = translated["description_es"]
                if translated.get("storyline_es"):
                    game.storyline_es = translated["storyline_es"]
                session.add(game)
                await session.commit()
                logger.info("[TRANSLATE] Cached Spanish copy for game %s", game.slug)
    except Exception:
        logger.exception("[TRANSLATE] Failed lazy Spanish translation for game %s", game_id)
