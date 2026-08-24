from __future__ import annotations

from fastapi import APIRouter

from api.services.quality_service import data_quality_report, pipeline_status, readiness

router = APIRouter(prefix="/api/v1", tags=["Operational Reliability"])


@router.get("/data-quality")
def get_data_quality() -> dict:
    return data_quality_report()


@router.get("/pipeline/status")
def get_pipeline_status() -> dict:
    return pipeline_status()


@router.get("/readiness")
def get_readiness() -> dict:
    return readiness()


@router.get("/climate-events")
def get_climate_events() -> dict:
    return {
        "status": "not_configured",
        "count": 0,
        "data": [],
        "message": "Connect the streaming weather pipeline to expose live climate events.",
    }
