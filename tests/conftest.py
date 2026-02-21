from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://usr:pwd@localhost:5432/testdb")
os.environ.setdefault("MLFLOW_TRACKING_URI", "sqlite:///:memory:")
