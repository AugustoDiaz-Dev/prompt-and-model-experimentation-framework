import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.reporting.report_generator import ReportGenerator
from app.db.models import Experiment, Metric, ABTest
import uuid

@pytest.mark.asyncio
async def test_experiment_report_generation(db_session: AsyncSession):
    # Setup data
    exp = Experiment(
        id=uuid.uuid4(),
        name="Report Logic Test",
        model_name="test-model",
        temperature=0.7,
        max_tokens=100
    )
    db_session.add(exp)
    metrics = [
        Metric(experiment_id=exp.id, metric_name="accuracy", value=0.9),
        Metric(experiment_id=exp.id, metric_name="accuracy", value=1.0),
        Metric(experiment_id=exp.id, metric_name="latency_ms", value=150.0),
    ]
    for m in metrics:
        db_session.add(m)
    await db_session.commit()
    
    generator = ReportGenerator(db_session)
    report = await generator.generate_experiment_report(exp.id)
    
    assert "Experiment Report" in report
    assert "Report Logic Test" in report
    assert "accuracy" in report
    assert "Mean: 0.950000" in report

@pytest.mark.asyncio
async def test_ab_test_report_generation(db_session: AsyncSession):
    # Setup two experiments
    def create_exp(name):
        return Experiment(id=uuid.uuid4(), name=name, model_name="m", temperature=0.7, max_tokens=1000)
    
    exp_a = create_exp("A")
    exp_b = create_exp("B")
    db_session.add_all([exp_a, exp_b])
    
    # Add metrics for both
    db_session.add(Metric(experiment_id=exp_a.id, metric_name="accuracy", value=0.8))
    db_session.add(Metric(experiment_id=exp_b.id, metric_name="accuracy", value=0.9))
    
    ab = ABTest(
        id=uuid.uuid4(),
        name="AB Report Test",
        experiment_a_id=exp_a.id,
        experiment_b_id=exp_b.id,
        traffic_split=0.5,
        p_value=0.04,
        significant=True,
        recommendation="B"
    )
    db_session.add(ab)
    await db_session.commit()
    
    generator = ReportGenerator(db_session)
    report_md = await generator.generate_ab_test_report(ab.id)
    report_html = await generator.generate_ab_test_report_html(ab.id)
    
    assert "# A/B Test Report" in report_md
    assert "**Significant**: Yes" in report_md
    assert "<html>" in report_html
    assert "<h2>Statistical Comparison</h2>" in report_html

@pytest.mark.asyncio
async def test_metrics_summary_empty(db_session: AsyncSession):
    exp = Experiment(id=uuid.uuid4(), name="Empty", model_name="m", temperature=0.7, max_tokens=1000)
    db_session.add(exp)
    await db_session.commit()
    
    generator = ReportGenerator(db_session)
    report = await generator.generate_experiment_report(exp.id)
    assert report is not None
