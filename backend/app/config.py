from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Authentication
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Visit tracking
    geofence_radius_m: int = 75
    visit_min_duration_seconds: int = 300
    visit_min_readings: int = 3

    # Google Maps API
    google_api_key: str = ""

    # Application
    debug: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
