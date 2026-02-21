from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), index=True)
    version: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    author: Mapped[str] = mapped_column(String(128))
    tags: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    experiments: Mapped[list["Experiment"]] = relationship(back_populates="prompt")


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), index=True)
    prompt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prompts.id", ondelete="SET NULL"), nullable=True, index=True
    )

    model_name: Mapped[str] = mapped_column(String(128))
    temperature: Mapped[float] = mapped_column(Numeric(5, 4))
    max_tokens: Mapped[int] = mapped_column()
    seed: Mapped[int | None] = mapped_column(nullable=True)

    mlflow_run_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    prompt: Mapped[Prompt | None] = relationship(back_populates="experiments")
    metrics: Mapped[list["Metric"]] = relationship(back_populates="experiment", cascade="all, delete-orphan")


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), index=True
    )

    metric_name: Mapped[str] = mapped_column(String(128), index=True)
    value: Mapped[float] = mapped_column(Numeric(12, 6))
    metric_metadata: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    experiment: Mapped[Experiment] = relationship(back_populates="metrics")


class ABTest(Base):
    __tablename__ = "ab_tests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), index=True)

    experiment_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), index=True
    )
    experiment_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), index=True
    )

    traffic_split: Mapped[float] = mapped_column(Numeric(5, 4))  # 0.0 to 1.0 (A gets this fraction)
    p_value: Mapped[float | None] = mapped_column(Numeric(10, 8), nullable=True)
    significant: Mapped[bool | None] = mapped_column(nullable=True)
    recommendation: Mapped[str | None] = mapped_column(String(32), nullable=True)  # A | B | inconclusive

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
