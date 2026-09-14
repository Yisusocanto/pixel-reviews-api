import logging

from fastapi import FastAPI

from src.auth.router import auth_router
from src.core.settings import settings
from src.games.router import router as games_router
from src.users.router import router as users_router

if settings.ENVIRONMENT == "development":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

app = FastAPI(
    title="Pixel Reviews API",
    description="API for Pixel Reviews with JWT Authentication & Refresh Token",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(games_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
