from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "src/.env"), extra="ignore")

    DATABASE_URL: str = ""
    API_RAWG_KEY: str = ""

    # JWT Auth Settings
    JWT_SECRET_KEY: str = "supersecret_jwt_key_change_me_in_production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cloudflare R2
    CF_ACCOUNT_ID: str
    CF_BUCKET: str
    CF_PUBLIC_URL: str
    CF_ACCESS_KEY_ID: str
    CF_SECRET_ACCESS_KEY: str

    ENVIRONMENT: str = "development"


settings = Settings()
