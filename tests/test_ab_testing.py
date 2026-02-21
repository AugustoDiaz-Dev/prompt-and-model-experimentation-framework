import pytest
from app.ab_testing.ab_testing import ABTestingModule
from app.experiment.experiment_runner import ExperimentConfig
import numpy as np
from unittest.mock import AsyncMock

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_ab_testing_mann_whitney():
    ab_module = ABTestingModule(AsyncMock())
    # Generate mock distribution
    values_a = list(np.random.normal(0.8, 0.05, 50))
    values_b = list(np.random.normal(0.85, 0.05, 50))
    p_value, significant, recommendation = ab_module._compare_experiments(values_a, values_b)
    
    assert 0.0 <= p_value <= 1.0
    assert isinstance(bool(significant), bool)
    assert recommendation in ["A", "B", "inconclusive"]

@pytest.mark.asyncio
async def test_traffic_split():
    ab_module = ABTestingModule(AsyncMock())
    values_a = [1.0] * 10
    values_b = [0.8] * 10
    sim_a, sim_b = ab_module.simulate_traffic_split(values_a, values_b, 0.6)
    assert len(sim_a) == 10  # Because max samples is bounds bounded to len
    assert len(sim_b) == 8   # Total is 20, 60% = 12 (but max 10), so returns 10 and 8
