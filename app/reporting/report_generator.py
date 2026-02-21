from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.db.models import ABTest, Experiment
from app.metrics.metrics import MetricsCalculator

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False



@dataclass(frozen=True)
class ExperimentReport:
    experiment_id: uuid.UUID
    experiment_name: str
    model_name: str
    temperature: float
    metrics_summary: dict[str, dict]
    recommendation: str | None = None


@dataclass(frozen=True)
class ABTestReport:
    ab_test_id: uuid.UUID
    ab_test_name: str
    experiment_a_name: str
    experiment_b_name: str
    p_value: float | None
    significant: bool | None
    recommendation: str | None
    metrics_comparison: dict[str, dict]


class ReportGenerator:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._metrics_calc = MetricsCalculator()

    async def generate_experiment_report(self, experiment_id: uuid.UUID) -> str:
        experiment = await self._session.get(Experiment, experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        summaries = self._metrics_calc.summarize_metrics(experiment)

        report_lines = [
            "# Experiment Report",
            "",
            f"**Experiment ID**: {experiment.id}",
            f"**Name**: {experiment.name}",
            f"**Model**: {experiment.model_name}",
            f"**Temperature**: {experiment.temperature}",
            f"**Max Tokens**: {experiment.max_tokens}",
            "",
            "## Metrics Summary",
            "",
        ]

        for metric_name, summary in summaries.items():
            ci_str = ""
            if summary.confidence_interval_95:
                ci_low, ci_high = summary.confidence_interval_95
                ci_str = f" (95% CI: {ci_low:.4f} - {ci_high:.4f})"
            report_lines.extend(
                [
                    f"### {metric_name}",
                    f"- Mean: {summary.mean:.6f}{ci_str}",
                    f"- Std Dev: {summary.std_dev:.6f}" if summary.std_dev else "- Std Dev: N/A",
                    f"- Min: {summary.min_value:.6f}",
                    f"- Max: {summary.max_value:.6f}",
                    f"- Count: {summary.count}",
                    "",
                ]
            )

        return "\n".join(report_lines)

    async def generate_ab_test_report(self, ab_test_id: uuid.UUID) -> str:
        ab_test = await self._session.get(ABTest, ab_test_id)
        if not ab_test:
            raise ValueError(f"AB test {ab_test_id} not found")

        exp_a = await self._session.get(Experiment, ab_test.experiment_a_id)
        exp_b = await self._session.get(Experiment, ab_test.experiment_b_id)

        if not exp_a or not exp_b:
            raise ValueError("Experiments not found")

        summaries_a = self._metrics_calc.summarize_metrics(exp_a)
        summaries_b = self._metrics_calc.summarize_metrics(exp_b)

        report_lines = [
            "# A/B Test Report",
            "",
            f"**AB Test ID**: {ab_test.id}",
            f"**Name**: {ab_test.name}",
            f"**Traffic Split**: {ab_test.traffic_split:.2%}",
            "",
            "## Experiments",
            "",
            f"### Experiment A: {exp_a.name}",
            f"- Model: {exp_a.model_name}",
            f"- Temperature: {exp_a.temperature}",
            "",
            f"### Experiment B: {exp_b.name}",
            f"- Model: {exp_b.model_name}",
            f"- Temperature: {exp_b.temperature}",
            "",
            "## Statistical Comparison",
            "",
        ]

        if ab_test.p_value is not None:
            report_lines.extend(
                [
                    f"- **P-value**: {ab_test.p_value:.6f}",
                    f"- **Significant**: {'Yes' if ab_test.significant else 'No'}",
                    f"- **Recommendation**: {ab_test.recommendation or 'N/A'}",
                    "",
                ]
            )

        report_lines.extend(["## Metrics Comparison", ""])

        # Compare common metrics
        common_metrics = set(summaries_a.keys()) & set(summaries_b.keys())
        for metric_name in common_metrics:
            sum_a = summaries_a[metric_name]
            sum_b = summaries_b[metric_name]
            diff = sum_a.mean - sum_b.mean
            diff_pct = (diff / sum_b.mean * 100) if sum_b.mean != 0 else 0.0

            report_lines.extend(
                [
                    f"### {metric_name}",
                    f"- A Mean: {sum_a.mean:.6f}",
                    f"- B Mean: {sum_b.mean:.6f}",
                    f"- Difference: {diff:.6f} ({diff_pct:+.2f}%)",
                    "",
                ]
            )

        return "\n".join(report_lines)

    async def generate_ab_test_report_html(self, ab_test_id: uuid.UUID) -> str:
        """Generates an HTML version of the A/B test report."""
        md_report = await self.generate_ab_test_report(ab_test_id)
        # Very simple MD to HTML conversion for demo purposes without external deps
        html_lines = ["<html><head><title>A/B Test Report</title>",
                      "<style>body{font-family:sans-serif;line-height:1.6;padding:20px;max-width:800px;margin:auto;}</style>",
                      "</head><body>"]
        
        for line in md_report.splitlines():
            if line.startswith("# "):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("- **") and "**:" in line:
                key, val = line[4:].split("**:", 1)
                html_lines.append(f"<li><strong>{key}</strong>:{val}</li>")
            elif line.startswith("- "):
                html_lines.append(f"<li>{line[2:]}</li>")
            elif line.startswith("**") and "**: " in line:
                key, val = line[2:].split("**: ", 1)
                html_lines.append(f"<p><strong>{key}</strong>: {val}</p>")
            elif line.strip() == "":
                pass
            else:
                html_lines.append(f"<p>{line}</p>")

        # Add Visualizations if Plotly is available
        if PLOTLY_AVAILABLE:
            fig_html = await self._generate_ab_test_charts(ab_test_id)
            if fig_html:
                html_lines.append("<h2>Visualizations</h2>")
                html_lines.append(fig_html)

        html_lines.append("</body></html>")
        return "\n".join(html_lines)

    async def _generate_ab_test_charts(self, ab_test_id: uuid.UUID) -> str | None:
        """Helper to generate Plotly HTML string blocks for metrics comparison."""
        ab_test = await self._session.get(ABTest, ab_test_id)
        if not ab_test:
            return None

        exp_a = await self._session.get(Experiment, ab_test.experiment_a_id)
        exp_b = await self._session.get(Experiment, ab_test.experiment_b_id)
        if not exp_a or not exp_b:
            return None

        summaries_a = self._metrics_calc.summarize_metrics(exp_a)
        summaries_b = self._metrics_calc.summarize_metrics(exp_b)
        
        common_metrics = sorted(list(set(summaries_a.keys()) & set(summaries_b.keys())))
        if not common_metrics:
            return None

        means_a = [summaries_a[m].mean for m in common_metrics]
        means_b = [summaries_b[m].mean for m in common_metrics]
        
        fig = go.Figure(data=[
            go.Bar(name=f'A: {exp_a.name}', x=common_metrics, y=means_a),
            go.Bar(name=f'B: {exp_b.name}', x=common_metrics, y=means_b)
        ])
        fig.update_layout(
            barmode='group', 
            title=f'A/B Test Comparison: {ab_test.name}',
            template="plotly_white",
            height=500
        )
        # Returns raw embeddable HTML string for the chart
        chart_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        return chart_html

