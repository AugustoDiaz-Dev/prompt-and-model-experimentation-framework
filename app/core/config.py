from __future__ import annotations

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"

    database_url: str = "sqlite+aiosqlite:///./test.db"
    mlflow_tracking_uri: str = ""
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    @property
    def is_serverless(self) -> bool:
        """Detect if we're running on Vercel serverless."""
        return bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))


settings = Settings()
