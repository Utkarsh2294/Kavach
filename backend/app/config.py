"""
Kavach Backend — Application Configuration.

Reads all settings from environment variables (via .env file).
Single source of truth for database URLs, Redis URL, secrets, etc.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://kavach:kavach_dev_password@localhost:5432/kavach"
    database_url_sync: str = "postgresql+psycopg2://kavach:kavach_dev_password@localhost:5432/kavach"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Application
    secret_key: str = "dev-secret-key-change-in-production"
    environment: str = "development"
    debug: bool = True

    # Auth (Phase 07 will use these)
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — call this instead of Settings() directly."""
    return Settings()
