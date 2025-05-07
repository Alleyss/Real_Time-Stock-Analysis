# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache # For caching the settings object

class Settings(BaseSettings):
    PROJECT_NAME: str = "Stock Analyzer API"
    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # API keys for services (will be used later)
    NEWSAPI_KEY: str | None = None # str or None if not set
    REDDIT_CLIENT_ID: str | None = None
    REDDIT_CLIENT_SECRET: str | None = None
    REDDIT_USER_AGENT: str | None = "StockAPI/0.1 by default_user" # Provide a default

    # Model config (will be used later)
    DEFAULT_SENTIMENT_MODEL: str = "ProsusAI/finbert"

    # Pydantic V2 way to specify .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')


@lru_cache()
def get_settings():
    return Settings()

settings = get_settings() # Global settings object