"""Phase 4B trained machine-learning API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from api.ml_schemas import MLAnomalyRequest, MLForecastRequest
from api.services.ml_service import MLService

router = APIRouter(prefix="/api/v1/ml", tags=["Phase 4B AI & Machine Learning"])


def _service() -> MLService:
    return MLService()


@router.get("/readiness")
def ml_readiness() -> dict[str, Any]:
    return _service().readiness()


@router.get("/models")
def model_registry() -> dict[str, Any]:
    try:
        return _service().registry()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.get("/training-report")
def training_report() -> dict[str, Any]:
    try:
        return _service().training_report()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/forecast")
def ml_forecast(request: MLForecastRequest) -> dict[str, Any]:
    try:
        return _service().forecast(
            request.country,
            request.indicator,
            request.horizon_years,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/anomaly/predict")
def ml_anomaly_prediction(request: MLAnomalyRequest) -> dict[str, Any]:
    try:
        return _service().anomaly_prediction(
            country=request.country,
            indicator=request.indicator,
            year=request.year,
            value=request.value,
            previous_value=request.previous_value,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/drift")
def model_drift() -> dict[str, Any]:
    try:
        return _service().drift_report()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
