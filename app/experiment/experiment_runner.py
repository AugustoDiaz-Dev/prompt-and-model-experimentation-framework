from __future__ import annotations

import asyncio
import logging
import random
import time
import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Experiment, Metric
from app.registry.prompt_registry import PromptRegistry
from app.metrics.hallucination import HallucinationDetector
from app.mlflow_integration.mlflow_tracker import MLflowTracker, MLFLOW_AVAILABLE
from app.experiment.llm_client import LLMClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    prompt_name: str | None = None
    prompt_version: int | None = None
    prompt_content: str | None = None
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 1000
    seed: int | None = None


@dataclass(frozen=True)
class ExperimentResult:
    experiment_id: uuid.UUID
    accuracy: float
    latency_ms: float
    cost_usd: float
    hallucination_rate: float | None = None


class ExperimentRunner:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._prompt_registry = PromptRegistry(session)
        self._hallucination_detector = HallucinationDetector()
        self._tracker = MLflowTracker() if MLFLOW_AVAILABLE else None
        self._llm_client = LLMClient()

    async def run(self, config: ExperimentConfig, test_cases: list[dict]) -> ExperimentResult:
        # Resolve prompt
        prompt = None
        if config.prompt_name:
            if config.prompt_version:
                prompt = await self._prompt_registry.get_by_version(config.prompt_name, config.prompt_version)
            else:
                prompt = await self._prompt_registry.get_latest(config.prompt_name)

        prompt_content = prompt.content if prompt else (config.prompt_content or "")

        # Set seed if provided
        if config.seed is not None:
            random.seed(config.seed)

        # Create experiment record
        experiment = Experiment(
            name=config.name,
            prompt_id=prompt.id if prompt else None,
            model_name=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            seed=config.seed,
        )
        self._session.add(experiment)
        await self._session.flush()

        # Run experiment (mock implementation for first step)
        start_time = time.time()
        results = await self._execute_test_cases(prompt_content, config, test_cases)
        elapsed_ms = (time.time() - start_time) * 1000

        # Calculate metrics
        accuracy = self._calculate_accuracy(results)
        cost = self._estimate_cost(config, len(test_cases))
        hallucination_rate = self._calculate_hallucination_rate(results)

        # Calculate extra metrics
        total_prompt_tokens = sum(r.get("usage", {}).get("prompt_tokens", 0) for r in results)
        total_comp_tokens = sum(r.get("usage", {}).get("completion_tokens", 0) for r in results)
        avg_quality_score = self._calculate_similarity_score(results)

        # Integrate with MLflow
        mlflow_run_id = None
        if self._tracker:
            try:
                mlflow_run_id = self._tracker.start_run(
                    experiment_name=config.name,
                    run_name=f"Run_{experiment.id}"
                )
                self._tracker.log_params({
                    "model_name": config.model_name,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                    "seed": config.seed,
                    "prompt_version": config.prompt_version,
                })
                self._tracker.log_metrics({
                    "accuracy": accuracy,
                    "latency_ms": elapsed_ms,
                    "cost_usd": cost,
                    "hallucination_rate": hallucination_rate,
                    "prompt_tokens": float(total_prompt_tokens),
                    "completion_tokens": float(total_comp_tokens),
                    "quality_score": avg_quality_score,
                })
                self._tracker.log_text(prompt_content, "prompt.txt")
                self._tracker.end_run()
                experiment.mlflow_run_id = mlflow_run_id
            except Exception as e:
                logger.warning("mlflow_tracking_failed", extra={"error": str(e)})

        # Store metrics
        self._session.add(Metric(experiment_id=experiment.id, metric_name="accuracy", value=accuracy))
        self._session.add(Metric(experiment_id=experiment.id, metric_name="latency_ms", value=elapsed_ms))
        self._session.add(Metric(experiment_id=experiment.id, metric_name="cost_usd", value=cost))
        self._session.add(Metric(experiment_id=experiment.id, metric_name="prompt_tokens", value=float(total_prompt_tokens)))
        self._session.add(Metric(experiment_id=experiment.id, metric_name="completion_tokens", value=float(total_comp_tokens)))
        self._session.add(Metric(experiment_id=experiment.id, metric_name="quality_score", value=avg_quality_score))

        if hallucination_rate is not None:
            self._session.add(
                Metric(experiment_id=experiment.id, metric_name="hallucination_rate", value=hallucination_rate)
            )

        await self._session.commit()

        logger.info(
            "experiment_completed",
            extra={
                "experiment_id": str(experiment.id),
                "accuracy": accuracy,
                "latency_ms": elapsed_ms,
            },
        )

        return ExperimentResult(
            experiment_id=experiment.id,
            accuracy=accuracy,
            latency_ms=elapsed_ms,
            cost_usd=cost,
            hallucination_rate=hallucination_rate,
        )

    async def _execute_test_cases(self, prompt: str, config: ExperimentConfig, test_cases: list[dict]) -> list[dict]:
        results = []
        for case in test_cases:
            input_text = case.get("input", "")
            
            output_content, usage = await self._llm_client.generate_response(
                prompt=prompt,
                input_text=input_text,
                model_name=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                seed=config.seed
            )
            
            results.append({
                "input": input_text,
                "output": output_content,
                "expected": case.get("expected"),
                "context": case.get("context"),
                "usage": usage
            })
        return results

    def _calculate_accuracy(self, results: list[dict]) -> float:
        if not results:
            return 0.0
        correct = sum(1 for r in results if r.get("output") == r.get("expected"))
        return correct / len(results)

    def _estimate_cost(self, config: ExperimentConfig, num_cases: int) -> float:
        # Rough cost estimation (mock)
        base_cost_per_call = 0.002  # $0.002 per call
        return base_cost_per_call * num_cases

    def _calculate_hallucination_rate(self, results: list[dict]) -> float:
        if not results:
            return 0.0
        total_rate = 0.0
        for r in results:
            output = r.get("output", "")
            context = r.get("context", None)  # Assume test case provides context if any
            h_result = self._hallucination_detector.detect(output, context)
            total_rate += h_result.hallucination_rate
        return total_rate / len(results)

    def _calculate_similarity_score(self, results: list[dict]) -> float:
        # A simple response quality score heuristic based on substring match or length ratio
        if not results:
            return 0.0
        total_score = 0.0
        for r in results:
            expected = str(r.get("expected", "")).lower()
            output = str(r.get("output", "")).lower()
            if not expected:
                total_score += 1.0
                continue
            if expected in output:
                total_score += 1.0
            else:
                total_score += 0.5 if len(output) > 0 and (len(expected) / 2) < len(output) < (len(expected) * 2) else 0.0
        return total_score / len(results)
