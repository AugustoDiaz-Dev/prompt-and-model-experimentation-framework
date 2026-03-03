from __future__ import annotations

import logging

from app.core.config import settings
from app.db.models import Base

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Create all tables. Works on both Vercel (sync) and local (async)."""
    if settings.is_serverless:
        from app.db.session import sync_engine
        if sync_engine:
            Base.metadata.create_all(bind=sync_engine)
            logger.info("database_initialized (sync/serverless)")
    else:
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_initialized (async)")
