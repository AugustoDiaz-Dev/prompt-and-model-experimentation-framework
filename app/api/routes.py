from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.ab_testing.ab_testing import ABTestingModule
from app.db.models import Experiment
from app.db.session import get_session
from app.experiment.experiment_runner import ExperimentConfig, ExperimentRunner
from app.registry.prompt_registry import PromptRegistry
from app.reporting.report_generator import ReportGenerator
from app.schemas import (
    ABTestCreateRequest,
    ABTestResponse,
    ExperimentCreateRequest,
    ExperimentResponse,
    PromptCreateRequest,
    PromptResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/prompts", response_model=PromptResponse)
async def create_prompt(
    payload: PromptCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> PromptResponse:
    registry = PromptRegistry(session)
    prompt_id = await registry.register(
        name=payload.name,
        content=payload.content,
        author=payload.author,
        tags=payload.tags,
    )
    await session.commit()

    prompt = await registry.get_latest(payload.name)
    if not prompt:
        raise HTTPException(status_code=500, detail="Failed to retrieve created prompt")

    return PromptResponse(
        id=prompt.id,
        name=prompt.name,
        version=prompt.version,
        content=prompt.content,
        author=prompt.author,
        tags=prompt.tags,
        created_at=prompt.created_at,
    )

@router.get("/prompts/{name}/compare")
async def compare_prompts(
    name: str,
    version_a: int,
    version_b: int,
    session: AsyncSession = Depends(get_session)
) -> dict:
    registry = PromptRegistry(session)
    try:
        comparison = await registry.compare(name, version_a, version_b)
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))



@router.get("/prompts", response_model=list[PromptResponse])
async def list_prompts(session: AsyncSession = Depends(get_session)) -> list[PromptResponse]:
    registry = PromptRegistry(session)
    prompts = await registry.list_all()
    return [
        PromptResponse(
            id=p.id,
            name=p.name,
            version=p.version,
            content=p.content,
            author=p.author,
            tags=p.tags,
            created_at=p.created_at,
        )
        for p in prompts
    ]


@router.post("/experiments", response_model=ExperimentResponse)
async def create_experiment(
    payload: ExperimentCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> ExperimentResponse:
    runner = ExperimentRunner(session)
    config = ExperimentConfig(
        name=payload.name,
        prompt_name=payload.prompt_name,
        prompt_version=payload.prompt_version,
        prompt_content=payload.prompt_content,
        model_name=payload.model_name,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        seed=payload.seed,
    )

    result = await runner.run(config, payload.test_cases)

    return ExperimentResponse(
        id=result.experiment_id,
        name=payload.name,
        model_name=payload.model_name,
        temperature=payload.temperature,
        accuracy=result.accuracy,
        latency_ms=result.latency_ms,
        cost_usd=result.cost_usd,
    )


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ExperimentResponse:
    experiment = await session.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get metrics
    accuracy_metric = next((m for m in experiment.metrics if m.metric_name == "accuracy"), None)
    latency_metric = next((m for m in experiment.metrics if m.metric_name == "latency_ms"), None)
    cost_metric = next((m for m in experiment.metrics if m.metric_name == "cost_usd"), None)

    return ExperimentResponse(
        id=experiment.id,
        name=experiment.name,
        model_name=experiment.model_name,
        temperature=float(experiment.temperature),
        accuracy=float(accuracy_metric.value) if accuracy_metric else 0.0,
        latency_ms=float(latency_metric.value) if latency_metric else 0.0,
        cost_usd=float(cost_metric.value) if cost_metric else 0.0,
    )


@router.post("/ab-tests", response_model=ABTestResponse)
async def create_ab_test(
    payload: ABTestCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> ABTestResponse:
    ab_module = ABTestingModule(session)
    ab_test = await ab_module.run_ab_test(
        name=payload.name,
        experiment_a_id=payload.experiment_a_id,
        experiment_b_id=payload.experiment_b_id,
        traffic_split=payload.traffic_split,
        metric_name=payload.metric_name,
    )

    return ABTestResponse(
        id=ab_test.id,
        name=ab_test.name,
        experiment_a_id=ab_test.experiment_a_id,
        experiment_b_id=ab_test.experiment_b_id,
        traffic_split=float(ab_test.traffic_split),
        p_value=float(ab_test.p_value) if ab_test.p_value else None,
        significant=ab_test.significant,
        recommendation=ab_test.recommendation,
    )


@router.get("/reports/{experiment_id}")
async def get_experiment_report(
    experiment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    generator = ReportGenerator(session)
    report = await generator.generate_experiment_report(experiment_id)
    return {"report": report}

from fastapi.responses import HTMLResponse

@router.get("/reports/ab-test/{ab_test_id}/html", response_class=HTMLResponse)
async def get_ab_test_report_html(
    ab_test_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    generator = ReportGenerator(session)
    try:
        report_html = await generator.generate_ab_test_report_html(ab_test_id)
        return HTMLResponse(content=report_html, status_code=200)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

async def _save_report_to_disk(experiment_id: uuid.UUID) -> None:
    # Use your own session to avoid closing conflicts with the request
    from app.db.session import async_session_maker
    async with async_session_maker() as session:
        generator = ReportGenerator(session)
        try:
            report_content = await generator.generate_experiment_report(experiment_id)
            import os
            os.makedirs("reports_output", exist_ok=True)
            file_path = f"reports_output/experiment_{experiment_id}_report.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report_content)
        except Exception as e:
            logger.error(f"Failed to generate automated report for {experiment_id}: {e}")

@router.post("/reports/experiments/{experiment_id}/automate")
async def automate_experiment_report(
    experiment_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session)
) -> dict[str, str]:
    # Validate it exists
    experiment = await session.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    background_tasks.add_task(_save_report_to_disk, experiment_id)
    return {"message": "Report generation started in the background", "experiment_id": str(experiment_id)}

