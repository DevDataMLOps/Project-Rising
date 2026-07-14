from typing import Any

from fastapi import APIRouter, Query


router = APIRouter(
    tags=["Climate Data"],
)


@router.get("/climate-events")
def list_climate_events(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
) -> dict[str, Any]:
    """Return accepted climate events when streaming is configured."""

    return {
        "status": "not_configured",
        "count": 0,
        "limit": limit,
        "data": [],
        "message": (
            "No accepted climate-event output file exists in "
            "the current repository. Run or implement the "
            "streaming pipeline to populate this endpoint."
        ),
    }