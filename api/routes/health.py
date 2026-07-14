from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.services.data_service import (
    get_countries,
    get_health_indicators,
    get_indicators,
)


router = APIRouter(
    prefix="/health-indicators",
    tags=["Health Data"],
)


@router.get("")
def list_health_indicators(
    country: str | None = Query(default=None),
    indicator: str | None = Query(default=None),
    year: int | None = Query(
        default=None,
        ge=1900,
        le=2100,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
) -> dict[str, Any]:
    """Return processed ASEAN health indicators."""

    try:
        records = get_health_indicators(
            country=country,
            indicator=indicator,
            year=year,
            limit=limit,
        )
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "count": len(records),
        "filters": {
            "country": country,
            "indicator": indicator,
            "year": year,
            "limit": limit,
        },
        "data": records,
    }


@router.get("/countries")
def list_countries() -> dict[str, Any]:
    """Return countries available in the processed dataset."""

    try:
        countries = get_countries()
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "count": len(countries),
        "countries": countries,
    }


@router.get("/indicators")
def list_indicators() -> dict[str, Any]:
    """Return indicators available in the processed dataset."""

    try:
        indicators = get_indicators()
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    return {
        "count": len(indicators),
        "indicators": indicators,
    }