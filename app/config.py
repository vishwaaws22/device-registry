"""Settings read from environment variables (never hard-code secrets)."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str
    heartbeat_timeout_seconds: int
    allowed_cities: tuple[str, ...]


def get_settings() -> Settings:
    cities = os.environ.get("ALLOWED_CITIES", "pune,mumbai,delhi")
    return Settings(
        app_env=os.environ.get("APP_ENV", "local"),
        heartbeat_timeout_seconds=int(os.environ.get("HEARTBEAT_TIMEOUT_SECONDS", "120")),
        allowed_cities=tuple(c.strip().lower() for c in cities.split(",") if c.strip()),
    )
