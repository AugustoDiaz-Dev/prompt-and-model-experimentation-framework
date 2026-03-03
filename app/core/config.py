from __future__ import annotations

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"

    database_url: str = "sqlite+aiosqlite:///./test.db"
    mlflow_tracking_uri: str = "http://localhost:5000"
    openai_api_key: str | None = None

    @property
    def sync_database_url(self) -> str:
        """Return a synchronous-compatible DB URL for Vercel / serverless.

        Supabase gives URLs like:
          postgresql://user:pass@host:port/db
        We need to make sure we use psycopg2 (sync) driver for serverless.
        """
        url = self.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        if url.startswith("sqlite+aiosqlite://"):
            return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return url

    @property
    def async_database_url(self) -> str:
        """Return an async-compatible DB URL for local development."""
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql+psycopg2://"):
            return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        if url.startswith("sqlite://") and "+aiosqlite" not in url:
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url

    @property
    def is_serverless(self) -> bool:
        """Detect if we're running on Vercel serverless."""
        return bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))


settings = Settings()
