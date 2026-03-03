from __future__ import annotations

import logging
import os

from app.db.models import Base

logger = logging.getLogger(__name__)

_IS_SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))


async def init_db() -> None:
    """Create all tables. Works on both Vercel (sync) and local (async)."""
    if _IS_SERVERLESS:
        from app.db.session import sync_engine
        if sync_engine:
            Base.metadata.create_all(bind=sync_engine)
            logger.info("database_initialized (sync/serverless)")
    else:
        from app.db.session import engine
        if engine:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("database_initialized (async)")
