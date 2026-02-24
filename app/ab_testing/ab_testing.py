from __future__ import annotations

import logging
import uuid

import math

from scipy import stats
import numpy as np

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ABTest, Experiment
from app.metrics.metrics import MetricsCalculator

logger = logging.getLogger(__name__)


class ABTestingModule:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._metrics_calc = MetricsCalculator()

    async def run_ab_test(
        self,
        *,
        name: str,
        experiment_a_id: uuid.UUID,
        experiment_b_id: uuid.UUID,
        traffic_split: float = 0.5,
        metric_name: str = "accuracy",
    ) -> ABTest:
        if not 0.0 <= traffic_split <= 1.0:
            raise ValueError("traffic_split must be between 0.0 and 1.0")

        stmt_a = select(Experiment).where(Experiment.id == experiment_a_id).options(joinedload(Experiment.metrics))
        stmt_b = select(Experiment).where(Experiment.id == experiment_b_id).options(joinedload(Experiment.metrics))
        
        result_a = await self._session.execute(stmt_a)
        result_b = await self._session.execute(stmt_b)
        
        exp_a = result_a.unique().scalar_one_or_none()
        exp_b = result_b.unique().scalar_one_or_none()

        if not exp_a or not exp_b:
            raise ValueError("One or both experiments not found")

        # Get metric values
        values_a = [float(m.value) for m in exp_a.metrics if m.metric_name == metric_name]
        values_b = [float(m.value) for m in exp_b.metrics if m.metric_name == metric_name]

        if not values_a or not values_b:
            raise ValueError(f"Insufficient {metric_name} metrics for comparison")

        # Statistical comparison
        p_value, significant, recommendation = self._compare_experiments(values_a, values_b)

        # Create AB test record
        ab_test = ABTest(
            name=name,
            experiment_a_id=experiment_a_id,
            experiment_b_id=experiment_b_id,
            traffic_split=traffic_split,
            p_value=p_value,
            significant=significant,
            recommendation=recommendation,
        )
        self._session.add(ab_test)
        await self._session.commit()

        logger.info(
            "ab_test_completed",
            extra={
                "ab_test_id": str(ab_test.id),
                "p_value": p_value,
                "significant": significant,
                "recommendation": recommendation,
            },
        )

        return ab_test

    def _compare_experiments(
        self, values_a: list[float], values_b: list[float]
    ) -> tuple[float, bool, str]:
        if len(values_a) < 2 or len(values_b) < 2:
            return 0.5, False, "inconclusive"

        # Perform Mann-Whitney U test (non-parametric, better for robust metrics)
        u_stat, p_value = stats.mannwhitneyu(values_a, values_b, alternative='two-sided')
        significant = p_value < 0.05

        mean_a = sum(values_a) / len(values_a)
        mean_b = sum(values_b) / len(values_b)

        # Effect size (Cohen's d)
        pooled_std = math.sqrt(
            ((len(values_a) - 1) * np.var(values_a, ddof=1) + (len(values_b) - 1) * np.var(values_b, ddof=1))
            / (len(values_a) + len(values_b) - 2)
        ) if len(values_a) + len(values_b) > 2 else 1.0

        if pooled_std > 0:
            effect_size = abs(mean_a - mean_b) / pooled_std
        else:
            effect_size = 0.0

        if significant:
            # For latency/cost, lower is better. Assuming accuracy/etc for now, returning A/B based on mean.
            # It's better to explicitly handle metric polarity. But for default (accuracy), higher is better.
            recommendation = "A" if mean_a > mean_b else "B"
            logger.info("ab_test_significant_difference", extra={"effect_size": effect_size})
        else:
            recommendation = "inconclusive"

        return float(p_value), significant, recommendation

    def simulate_traffic_split(
        self, values_a: list[float], values_b: list[float], traffic_split: float
    ) -> tuple[list[float], list[float]]:
        # Simulate traffic allocation
        total_samples = len(values_a) + len(values_b)
        samples_a = int(total_samples * traffic_split)
        samples_b = total_samples - samples_a

        # Simple simulation: take first N samples from each
        simulated_a = values_a[:samples_a] if samples_a <= len(values_a) else values_a
        simulated_b = values_b[:samples_b] if samples_b <= len(values_b) else values_b

        return simulated_a, simulated_b
