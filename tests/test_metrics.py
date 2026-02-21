from app.metrics.metrics import MetricsCalculator, MetricSummary


def test_confidence_interval() -> None:
    calc = MetricsCalculator()
    values = [0.8, 0.85, 0.9, 0.75, 0.88]
    ci = calc.calculate_confidence_interval(values, confidence=0.95)
    assert ci is not None
    assert len(ci) == 2
    assert ci[0] < ci[1]


def test_confidence_interval_insufficient_data() -> None:
    calc = MetricsCalculator()
    values = [0.8]
    ci = calc.calculate_confidence_interval(values)
    assert ci is None
