from __future__ import annotations

from typing import Any

import pandas as pd

from api.repositories.health_repository import HealthRepository, repository


def country_profile(country: str, repo: HealthRepository = repository) -> dict[str, Any]:
    resolved = repo.resolve_country(country)
    latest = repo.latest_country_values(resolved)
    records = latest.astype(object).where(pd.notna(latest), None).to_dict(orient="records")
    years = [record["year"] for record in records]
    return {
        "country": resolved,
        "latest_year": max(years) if years else None,
        "indicator_count": len({record["indicator"] for record in records}),
        "data": records,
    }


def indicator_comparison(
    indicator: str,
    repo: HealthRepository = repository,
) -> dict[str, Any]:
    resolved = repo.resolve_indicator(indicator)
    dataframe = repo.latest_indicator_by_country(resolved)
    if dataframe.empty:
        return {"indicator": resolved, "asean_average": None, "count": 0, "data": []}

    dataframe = dataframe.sort_values("value", ascending=False)
    records = dataframe.astype(object).where(pd.notna(dataframe), None).to_dict(orient="records")
    return {
        "indicator": resolved,
        "asean_average": round(float(dataframe["value"].mean()), 3),
        "minimum": round(float(dataframe["value"].min()), 3),
        "maximum": round(float(dataframe["value"].max()), 3),
        "count": len(records),
        "data": records,
    }


def indicator_trend(
    country: str,
    indicator: str,
    repo: HealthRepository = repository,
) -> dict[str, Any]:
    resolved_country = repo.resolve_country(country)
    resolved_indicator = repo.resolve_indicator(indicator)
    dataframe = repo.trend(resolved_country, resolved_indicator)
    if dataframe.empty:
        return {
            "country": resolved_country,
            "indicator": resolved_indicator,
            "trend": "insufficient_data",
            "absolute_change": None,
            "percentage_change": None,
            "data": [],
        }

    first = float(dataframe.iloc[0]["value"])
    last = float(dataframe.iloc[-1]["value"])
    absolute_change = last - first
    percentage_change = None if first == 0 else (absolute_change / abs(first)) * 100
    tolerance = max(abs(first) * 0.01, 1e-9)
    direction = "stable"
    if absolute_change > tolerance:
        direction = "increasing"
    elif absolute_change < -tolerance:
        direction = "decreasing"

    records = dataframe.astype(object).where(pd.notna(dataframe), None).to_dict(orient="records")
    return {
        "country": resolved_country,
        "indicator": resolved_indicator,
        "trend": direction,
        "absolute_change": round(absolute_change, 3),
        "percentage_change": (
            round(float(percentage_change), 3) if percentage_change is not None else None
        ),
        "start_year": int(dataframe.iloc[0]["year"]),
        "end_year": int(dataframe.iloc[-1]["year"]),
        "data": records,
    }
