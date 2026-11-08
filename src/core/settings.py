from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "src/.env"), extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    TWITCH_CLIENT_ID: str = ""
    TWITCH_CLIENT_SECRET: str = ""
    TWITCH_AUTH_URL: str = "https://id.twitch.tv/oauth2/token"
    IGDB_API_URL: str = "https://api.igdb.com/v4"
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    JWT_SECRET_KEY: str = "supersecret_jwt_key_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_CLIENT_ID: str = ""
    RESEND_API_KEY: str = ""
    RESEND_DOMAIN: str = "onboarding@resend.dev"

    CF_ACCOUNT_ID: str
    CF_BUCKET: str
    CF_PUBLIC_URL: str
    CF_ACCESS_KEY_ID: str
    CF_SECRET_ACCESS_KEY: str

    ENVIRONMENT: str = "development"

    @model_validator(mode="after")
    def validate_production_secrets(self) -> Self:
        if self.ENVIRONMENT == "production" and (
            not self.JWT_SECRET_KEY
            or self.JWT_SECRET_KEY == "supersecret_jwt_key_change_me_in_production"
        ):
            raise ValueError("JWT_SECRET_KEY must be set to a secure value in production")
        return self


settings = Settings()
