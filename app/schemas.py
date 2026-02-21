from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PromptCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    content: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=128)
    tags: dict | None = None


class PromptResponse(BaseModel):
    id: uuid.UUID
    name: str
    version: int
    content: str
    author: str
    tags: dict
    created_at: datetime


class ExperimentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    prompt_name: str | None = None
    prompt_version: int | None = None
    prompt_content: str | None = None
    model_name: str = "gpt-3.5-turbo"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=100000)
    seed: int | None = None
    test_cases: list[dict] = Field(default_factory=list)


class ExperimentResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_name: str
    temperature: float
    accuracy: float
    latency_ms: float
    cost_usd: float


class ABTestCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    experiment_a_id: uuid.UUID
    experiment_b_id: uuid.UUID
    traffic_split: float = Field(default=0.5, ge=0.0, le=1.0)
    metric_name: str = "accuracy"


class ABTestResponse(BaseModel):
    id: uuid.UUID
    name: str
    experiment_a_id: uuid.UUID
    experiment_b_id: uuid.UUID
    traffic_split: float
    p_value: float | None
    significant: bool | None
    recommendation: str | None
