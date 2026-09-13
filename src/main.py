from fastapi import FastAPI

from src.auth.router import auth_router
from src.users.router import router as users_router

app = FastAPI(
    title="Pixel Reviews API",
    description="API for Pixel Reviews with JWT Authentication & Refresh Token",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
