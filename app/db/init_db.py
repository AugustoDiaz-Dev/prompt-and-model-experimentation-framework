from __future__ import annotations

import logging
from app.db.models import Base

logger = logging.getLogger(__name__)


async def init_db() -> None:
    """Create all tables using the async engine."""
    from app.db.session import engine
    if engine:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_initialized (async)")
