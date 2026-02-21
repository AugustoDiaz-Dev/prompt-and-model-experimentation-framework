from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import mlflow
    from mlflow.tracking import MlflowClient

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    logger.warning("MLflow not installed. Install with: pip install mlflow")


class MLflowTracker:
    def __init__(self):
        if not MLFLOW_AVAILABLE:
            raise ImportError("MLflow is not installed. Install with: pip install mlflow")
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        self._client = MlflowClient()

    def start_run(self, experiment_name: str, run_name: str | None = None) -> str:
        mlflow.set_experiment(experiment_name)
        run = mlflow.start_run(run_name=run_name)
        return run.info.run_id

    def log_params(self, params: dict[str, Any]) -> None:
        mlflow.log_params(params)

    def log_metrics(self, metrics: dict[str, float]) -> None:
        mlflow.log_metrics(metrics)

    def log_artifact(self, local_path: str, artifact_path: str | None = None) -> None:
        mlflow.log_artifact(local_path, artifact_path)

    def log_text(self, text: str, artifact_file: str) -> None:
        mlflow.log_text(text, artifact_file)


    def end_run(self) -> None:
        mlflow.end_run()

    def get_run(self, run_id: str) -> dict[str, Any]:
        run = self._client.get_run(run_id)
        return {
            "run_id": run.info.run_id,
            "experiment_id": run.info.experiment_id,
            "status": run.info.status,
            "params": run.data.params,
            "metrics": run.data.metrics,
        }
