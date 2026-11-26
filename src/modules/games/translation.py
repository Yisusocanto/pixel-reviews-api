import logging
import uuid

from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.db.database import async_session_maker
from src.modules.games.models import Game
from src.services.gemini.client import GeminiService

logger = logging.getLogger("game_translation")


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
