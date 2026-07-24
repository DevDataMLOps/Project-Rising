from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class DiseaseRiskRequest(BaseModel):
    country: str = Field(min_length=2, max_length=80)
    disease: Literal["dengue", "malaria", "mosquito_borne"]
    temperature_c: float = Field(ge=-20, le=60)
    rainfall_mm: float = Field(ge=0, le=5000)
    humidity_pct: float = Field(ge=0, le=100)
