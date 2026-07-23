from typing import Any

from fastapi import APIRouter, HTTPException, Path

from api.services.data_service import get_country_risk


router = APIRouter(
    prefix="/countries",
    tags=["Risk Intelligence"],
)


@router.get("/{country}/risk")
def country_risk(
    country: str = Path(min_length=2, max_length=100),
) -> dict[str, Any]:
    """Return a transparent comparative country-risk score."""

    try:
        return get_country_risk(country)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error
