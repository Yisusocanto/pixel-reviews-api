import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.core.settings import settings
from src.db.database import engine
from src.lib.limiter import limiter
from src.modules.auth.router import auth_router
from src.modules.comments.router import router as comments_router
from src.modules.games.router import router as games_router
from src.modules.reviews.router import router as review_router
from src.modules.users.router import router as users_router
from src.modules.wishlists.router import router as wishlists_router

if settings.ENVIRONMENT == "development":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    async with httpx.AsyncClient(timeout=10.0) as http_client:
        app.state.http_client = http_client
        app.state.redis = redis_client
        yield
    await redis_client.aclose()
    await engine.dispose()


app = FastAPI(
    title="Pixel Reviews API",
    description="API for Pixel Reviews",
    version="0.1.0",
    lifespan=lifespan,
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


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
