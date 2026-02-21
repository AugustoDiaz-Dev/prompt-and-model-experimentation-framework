from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models import Experiment


@dataclass(frozen=True)
class MetricSummary:
    metric_name: str
    mean: float
    std_dev: float | None
    min_value: float
    max_value: float
    count: int
    confidence_interval_95: tuple[float, float] | None = None


class MetricsCalculator:
    @staticmethod
    def calculate_confidence_interval(values: list[float], confidence: float = 0.95) -> tuple[float, float] | None:
        if len(values) < 2:
            return None

        mean = statistics.mean(values)
        if len(values) == 2:
            std_err = statistics.stdev(values) / (len(values) ** 0.5) if len(values) > 1 else 0.0
        else:
            std_err = statistics.stdev(values) / (len(values) ** 0.5)

        # Simplified: using z-score for 95% confidence (1.96)
        z_score = 1.96 if confidence == 0.95 else 1.645  # 90% fallback
        margin = z_score * std_err

        return (mean - margin, mean + margin)

    @staticmethod
    def summarize_metrics(experiment: "Experiment") -> dict[str, MetricSummary]:
        metric_values: dict[str, list[float]] = {}
        for metric in experiment.metrics:
            if metric.metric_name not in metric_values:
                metric_values[metric.metric_name] = []
            metric_values[metric.metric_name].append(float(metric.value))

        summaries: dict[str, MetricSummary] = {}
        for metric_name, values in metric_values.items():
            if not values:
                continue

            mean = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else None
            min_val = min(values)
            max_val = max(values)
            ci_95 = MetricsCalculator.calculate_confidence_interval(values, confidence=0.95)

            summaries[metric_name] = MetricSummary(
                metric_name=metric_name,
                mean=mean,
                std_dev=std_dev,
                min_value=min_val,
                max_value=max_val,
                count=len(values),
                confidence_interval_95=ci_95,
            )

        return summaries
