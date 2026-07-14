from typing import Any

from fastapi import APIRouter

from api.services.data_service import get_pipeline_status


router = APIRouter(
    prefix="/pipeline",
    tags=["Pipeline Monitoring"],
)


@router.get("/status")
def pipeline_status() -> dict[str, Any]:
    """Return the current batch and streaming pipeline status."""

    return get_pipeline_status()