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

    # Auth (Phase 07)
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ML / Intelligence Layer (Phase 08)
    # Artifacts dir resolves to the repo-root `ml/artifacts` by default.
    # Both models load once at startup; scoring runs in-process with zero
    # inference-time network calls (the hard Phase 08 constraint).
    ml_enabled: bool = True
    ml_artifacts_dir: str = ""  # empty -> auto-resolve to ../ml/artifacts
    ml_threshold_low: float = 0.30    # score <  low  -> approve  (rules passed)
    ml_threshold_high: float = 0.70   # score >= high -> deny ; middle -> escalate
    ml_max_history: int = 50          # recent txns used for rolling features

    # Real-time (Phase 09)
    spend_window_seconds: int = 3600  # rolling spend-cap window (1h)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def resolved_ml_artifacts_dir(self) -> str:
        import os
        if self.ml_artifacts_dir:
            return self.ml_artifacts_dir
        # backend/app/config.py -> repo root / ml / artifacts
        here = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.join(here, "..", "..", "ml", "artifacts"))

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — call this instead of Settings() directly."""
    return Settings()
