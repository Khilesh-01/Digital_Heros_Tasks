"""Centralized application configuration.

All tunable values live here and are sourced from environment variables so
behaviour can change per-environment without touching code.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General -----------------------------------------------------
    app_name: str = "Page Pulse API"
    app_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"

    # --- CORS ----------------------------------------------------------
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- HTTP client / fetcher ----------------------------------------
    request_timeout_seconds: float = 10.0
    connect_timeout_seconds: float = 5.0
    max_redirects: int = 5
    max_response_bytes: int = 5_000_000  # 5 MB cap to avoid huge downloads
    user_agent: str = "PagePulseBot/1.0 (+https://digitalheroesco.com)"
    max_retries: int = 2
    retry_backoff_seconds: float = 0.5

    # --- Security / SSRF guard -----------------------------------------
    allow_private_network_targets: bool = False
    allowed_schemes: str = "http,https"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_schemes_list(self) -> List[str]:
        return [s.strip().lower() for s in self.allowed_schemes.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton for the process)."""
    return Settings()
