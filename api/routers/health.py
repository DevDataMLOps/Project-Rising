from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.repositories.health_repository import DataUnavailableError, repository
from api.services.health_service import country_profile, indicator_comparison, indicator_trend
from api.services.risk_service import country_risk_score

router = APIRouter(prefix="/api/v1", tags=["Health Intelligence"])


@router.get("/health-indicators/countries")
def list_countries() -> dict:
    countries = repository.countries()
    return {"count": len(countries), "countries": countries}


@router.get("/health-indicators/indicators")
def list_indicators() -> dict:
    indicators = repository.indicators()
    return {"count": len(indicators), "indicators": indicators}


@router.get("/health-indicators/metadata")
def list_indicator_metadata() -> dict:
    data = repository.metadata_records()
    return {"count": len(data), "data": data}


@router.get("/health-indicators")
def get_health_indicators(
    country: str | None = None,
    indicator: str | None = None,
    year: int | None = Query(default=None, ge=1900, le=2100),
    sex: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict:
    try:
        total, data = repository.filter_records(
            country=country,
            indicator=indicator,
            year=year,
            sex=sex,
            offset=offset,
            limit=limit,
        )
    except DataUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"count": len(data), "total": total, "offset": offset, "limit": limit, "data": data}


@router.get("/countries/{country}/profile")
def get_country_profile(country: str) -> dict:
    try:
        return country_profile(country)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown country: {country}") from exc


@router.get("/health-indicators/compare/{indicator}")
def compare_indicator(indicator: str) -> dict:
    try:
        return indicator_comparison(indicator)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown indicator: {indicator}") from exc


@router.get("/health-indicators/trends")
def get_indicator_trend(country: str, indicator: str) -> dict:
    try:
        return indicator_trend(country, indicator)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown country or indicator") from exc


@router.get("/countries/{country}/risk")
def get_country_risk(country: str) -> dict:
    try:
        return country_risk_score(country)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown country: {country}") from exc
