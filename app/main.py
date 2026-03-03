from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging(settings.log_level)
    app = FastAPI(title="Prompt and Model Experimentation Framework", version="0.1.0")

    # Import routes lazily (they pull in db session)
    from app.api.routes import router
    app.include_router(router, prefix="/api")

    # Static files
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.on_event("startup")
    async def _startup() -> None:
        logging.getLogger(__name__).info("startup")
        from app.db.init_db import init_db
        await init_db()

    @app.get("/", include_in_schema=False)
    async def read_index():
        return FileResponse(os.path.join(static_dir, "index.html"))

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return FileResponse(os.path.join(static_dir, "favicon.png"), media_type="image/png")

    @app.get("/app", include_in_schema=False)
    async def read_dashboard():
        return FileResponse(os.path.join(static_dir, "dashboard.html"))

    return app


app = create_app()
