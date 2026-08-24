from typing import Any

from fastapi import APIRouter, Depends

from api.services.data_service import get_pipeline_status
from api.security import verify_api_key


router = APIRouter(
    prefix="/pipeline",
    tags=["Pipeline Monitoring"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("/status")
def pipeline_status() -> dict[str, Any]:
    """Return the current batch and streaming pipeline status."""

    return get_pipeline_status()
