from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from api.services.disease_risk_service import predict_disease_risk
from api.security import verify_api_key


router = APIRouter(
    prefix="/disease-risk",
    tags=["Disease Risk Prediction"],
)


class DiseaseRiskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    country: str = Field(min_length=2, max_length=100, examples=["Philippines"])
    disease: Literal["dengue", "malaria", "mosquito_borne"] = "dengue"
    temperature_c: float = Field(ge=-10, le=55, examples=[29.0])
    rainfall_mm: float = Field(ge=0, le=2000, examples=[180.0])
    humidity_pct: float = Field(ge=0, le=100, examples=[85.0])


def _predict(payload: DiseaseRiskRequest) -> dict[str, Any]:
    try:
        return predict_disease_risk(**payload.model_dump())
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post("/predict", dependencies=[Depends(verify_api_key)])
def disease_risk_prediction(payload: DiseaseRiskRequest) -> dict[str, Any]:
    """Predict explainable 14-day mosquito-borne disease risk."""

    return _predict(payload)


@router.get("/sample")
def sample_disease_risk_prediction() -> dict[str, Any]:
    """Return a judge-ready prediction using a wet-season Philippines scenario."""

    return _predict(
        DiseaseRiskRequest(
            country="Philippines",
            disease="dengue",
            temperature_c=29.0,
            rainfall_mm=180.0,
            humidity_pct=85.0,
        )
    )
