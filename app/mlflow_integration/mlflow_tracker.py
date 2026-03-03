from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# MLflow is optional — don't crash if not installed or URI not set
_mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "")

try:
    if not _mlflow_uri:
        raise ImportError("MLFLOW_TRACKING_URI not set, skipping MLflow")
    import mlflow
    from mlflow.tracking import MlflowClient

    MLFLOW_AVAILABLE = True
except ImportError as e:
    MLFLOW_AVAILABLE = False
    logger.info(f"MLflow disabled: {e}")


class MLflowTracker:
    def __init__(self):
        if not MLFLOW_AVAILABLE:
            raise ImportError("MLflow is not available")
        mlflow.set_tracking_uri(_mlflow_uri)
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
