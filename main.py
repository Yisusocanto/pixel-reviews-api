import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

import httpx
from aio_pika.exceptions import AMQPError
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from redis.exceptions import RedisError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.core.settings import settings
from src.db.database import SessionDep, engine
from src.lib.limiter import limiter
from src.modules.auth.router import auth_router
from src.modules.comments.router import router as comments_router
from src.modules.fav_user_games.router import router as fav_user_games_router
from src.modules.games.router import router as games_router
from src.modules.review_moderation.router import router as review_moderation_router
from src.modules.review_moderation.sweeper import run_sweeper_loop
from src.modules.reviews.router import router as review_router
from src.modules.users.router import router as users_router
from src.modules.wishlists.router import router as wishlists_router
from src.services.broker.client import Broker

IS_PRODUCTION = settings.ENVIRONMENT == "production"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    broker = Broker(settings.RABBITMQ_URL)
    try:
        await broker.setup_topology()
    except (AMQPError, OSError, TimeoutError) as exc:
        logger.warning("[BROKER] Could not initialize topology on startup: %s", exc)

    sweeper_task = asyncio.create_task(
        run_sweeper_loop(
            broker=broker,
            stale_minutes=settings.MODERATION_SWEEPER_STALE_MINUTES,
            interval_seconds=settings.MODERATION_SWEEPER_INTERVAL_SECONDS,
            batch_size=settings.MODERATION_SWEEPER_BATCH_SIZE,
            exchange_name="moderation",
            routing_key="moderation.review.check",
        )
    )

    redis_client = Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        health_check_interval=30,
        socket_keepalive=True,
        retry_on_timeout=True,
    )
    async with httpx.AsyncClient(timeout=10.0) as http_client:
        app.state.http_client = http_client
        app.state.redis = redis_client
        app.state.broker = broker
        yield
    await redis_client.aclose()
    await engine.dispose()
    sweeper_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await sweeper_task
    try:
        await broker.close()
    except (AMQPError, OSError, TimeoutError) as exc:
        logger.warning("[BROKER] Error closing broker pools: %s", exc)


app = FastAPI(
    title="Pixel Reviews API",
    description="API for Pixel Reviews",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if IS_PRODUCTION else "/docs",
    redoc_url=None if IS_PRODUCTION else "/redoc",
    openapi_url=None if IS_PRODUCTION else "/openapi.json",
)

app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "PATCH", "PUT", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(games_router)
app.include_router(review_router)
app.include_router(wishlists_router)
app.include_router(comments_router)
app.include_router(fav_user_games_router)
app.include_router(review_moderation_router)


@app.get("/health", tags=["Health"])
async def health_check(request: Request, response: Response, session: SessionDep):
    checks = {"database": "ok", "redis": "ok"}

    try:
        await session.exec(text("SELECT 1"))
    except SQLAlchemyError:
        logger.exception("[HEALTH] Database check failed")
        checks["database"] = "unavailable"

    redis_client: Redis | None = getattr(request.app.state, "redis", None)
    if redis_client is None:
        checks["redis"] = "unavailable"
    else:
        try:
            await redis_client.ping()
        except RedisError:
            logger.warning("[HEALTH] Redis check failed")
            checks["redis"] = "unavailable"

    if checks["database"] != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unhealthy", **checks}

    if checks["redis"] != "ok":
        return {"status": "degraded", **checks}

    return {"status": "ok", **checks}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
