from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.schemas import DiseaseRiskRequest
from api.services.anomaly_service import detect_anomalies
from api.services.disease_risk_service import predict_disease_risk

router = APIRouter(prefix="/api/v1", tags=["AI and Risk Intelligence"])


@router.post("/disease-risk/predict")
def disease_risk_prediction(request: DiseaseRiskRequest) -> dict:
    try:
        return predict_disease_risk(**request.model_dump())
    except AttributeError:
        # Pydantic v1 compatibility.
        try:
            return predict_disease_risk(**request.dict())
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown country or disease") from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown country or disease") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/disease-risk/sample")
def disease_risk_sample() -> dict:
    return predict_disease_risk(
        country="Philippines",
        disease="dengue",
        temperature_c=29.0,
        rainfall_mm=180.0,
        humidity_pct=85.0,
    )


@router.get("/anomalies")
def anomalies(
    country: str | None = None,
    indicator: str | None = None,
    z_threshold: float = Query(default=2.5, ge=1.0, le=10.0),
    limit: int = Query(default=50, ge=1, le=500),
) -> dict:
    try:
        return detect_anomalies(
            country=country,
            indicator=indicator,
            z_threshold=z_threshold,
            limit=limit,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown country or indicator") from exc
