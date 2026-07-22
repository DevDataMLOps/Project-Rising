"""Pydantic contracts for Phase 4 operational intelligence."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


EventType = Literal[
    "pipeline_failure",
    "data_quality",
    "api_health",
    "climate_risk",
    "disease_risk",
    "recovery",
]
EventStatus = Literal[
    "info",
    "healthy",
    "warning",
    "degraded",
    "error",
    "failed",
    "critical",
    "recovered",
]


class OperationalEvent(BaseModel):
    """A normalized signal received from a pipeline, API, or risk engine."""

    event_type: EventType
    source: str = Field(min_length=2, max_length=100)
    status: EventStatus = "warning"
    message: str = Field(min_length=3, max_length=1000)
    country: str | None = Field(default=None, max_length=100)
    metric: str | None = Field(default=None, max_length=100)
    value: float | None = None
    threshold: float | None = None
    observed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AcknowledgeRequest(BaseModel):
    """Human acknowledgement details for an operational alert."""

    owner: str = Field(default="public-health-operations", min_length=2, max_length=100)
    note: str | None = Field(default=None, max_length=500)


class EvaluateRequest(BaseModel):
    """Thresholds used when evaluating the current repository state."""

    stale_after_hours: int = Field(default=720, ge=1, le=8760)
    anomaly_limit: int = Field(default=10, ge=1, le=100)
    include_anomalies: bool = True
