from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator

from app.core.config import settings

logger = logging.getLogger(__name__)

# Detect serverless environment at module level
_IS_SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))


if _IS_SERVERLESS:
    # ---- VERCEL / SERVERLESS: use synchronous psycopg2 only ----
    from sqlalchemy import create_engine as create_sync_engine
    from sqlalchemy.orm import Session, sessionmaker

    def _get_sync_url() -> str:
        url = settings.database_url
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return url

    _sync_url = _get_sync_url()
    logger.info(f"Serverless mode: using sync engine ({_sync_url.split('://')[0]})")

    sync_engine = create_sync_engine(_sync_url, pool_pre_ping=True)
    SyncSessionLocal = sessionmaker(sync_engine, expire_on_commit=False)

    # Provide a thin async-compatible wrapper so FastAPI Depends still works
    async def get_session() -> AsyncIterator[Session]:
        session = SyncSessionLocal()
        try:
            yield session
        finally:
            session.close()

    engine = None
    SessionLocal = None

else:
    # ---- LOCAL DEV: use async engine (asyncpg) ----
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    def _get_async_url() -> str:
        url = settings.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgresql+psycopg2://"):
            return url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
        if url.startswith("sqlite://") and "+aiosqlite" not in url:
            return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        return url

    _async_url = _get_async_url()
    logger.info(f"Local mode: using async engine ({_async_url.split('://')[0]})")

    engine = create_async_engine(_async_url, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def get_session() -> AsyncIterator[AsyncSession]:
        async with SessionLocal() as session:
            yield session

    sync_engine = None
    SyncSessionLocal = None
