"""
core/config.py

Central app settings, loaded from environment / .env via pydantic-settings.
Everything that varies between dev, docker-compose, and prod should be
read from here, never hardcoded in models/queries/api files.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Matches docker-compose.yml's `backend.environment.DATABASE_URL` and
    # migrations/env.py's os.getenv("DATABASE_URL") — keep all three in sync.
    DATABASE_URL: str = "postgresql://ktm_bus:ktm_bus_dev@localhost:5432/ktm_bus_route_finder"

    # Default radius (meters) for GET /stops/nearby when the caller omits it.
    DEFAULT_NEARBY_RADIUS_M: int = 500

    # Default / max page size for GET /stops.
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 200

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Cached so we parse the environment once per process."""
    return Settings()