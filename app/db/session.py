from __future__ import annotations

import logging
from collections.abc import AsyncIterator

from sqlalchemy import create_engine as create_sync_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# --- Async engine (for local dev with uvicorn) ---
def _create_async_engine() -> AsyncEngine:
    db_url = settings.async_database_url
    logger.info(f"Creating async engine with URL scheme: {db_url.split('://')[0]}")
    return create_async_engine(db_url, pool_pre_ping=True)


# --- Sync engine (for Vercel serverless) ---
def _create_sync_engine():
    db_url = settings.sync_database_url
    logger.info(f"Creating sync engine with URL scheme: {db_url.split('://')[0]}")
    return create_sync_engine(db_url, pool_pre_ping=True)


if settings.is_serverless:
    # On Vercel: use synchronous engine
    sync_engine = _create_sync_engine()
    SyncSessionLocal = sessionmaker(sync_engine, expire_on_commit=False)

    # Still create a thin async wrapper for compatibility
    engine = _create_async_engine()
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
else:
    # Local dev: use async engine
    engine = _create_async_engine()
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sync_engine = None
    SyncSessionLocal = None


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
