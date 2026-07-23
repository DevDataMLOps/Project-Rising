"""Pydantic contracts for Phase 4B machine-learning endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MLForecastRequest(BaseModel):
    country: str = Field(min_length=2, examples=["Philippines"])
    indicator: str = Field(min_length=2, examples=["life_expentancy_rate"])
    horizon_years: int = Field(default=3, ge=1, le=5)


class MLAnomalyRequest(BaseModel):
    country: str = Field(min_length=2, examples=["Philippines"])
    indicator: str = Field(min_length=2, examples=["infant_mortality_rate"])
    year: int = Field(ge=1900, le=2100, examples=[2025])
    value: float = Field(examples=[18.4])
    previous_value: float | None = Field(
        default=None,
        description=(
            "Optional previous annual value. When omitted, the latest baseline value "
            "for the country and indicator is used."
        ),
    )
