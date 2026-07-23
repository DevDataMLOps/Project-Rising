from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from api.repositories.health_repository import HealthRepository, repository


def detect_anomalies(
    *,
    country: str | None = None,
    indicator: str | None = None,
    z_threshold: float = 2.5,
    limit: int = 50,
    repo: HealthRepository = repository,
) -> dict[str, Any]:
    dataframe = repo.load_health_data().copy()
    if country:
        resolved_country = repo.resolve_country(country)
        dataframe = dataframe[dataframe["country"] == resolved_country]
    if indicator:
        resolved_indicator = repo.resolve_indicator(indicator)
        dataframe = dataframe[dataframe["indicator"] == resolved_indicator]

    anomalies: list[dict[str, Any]] = []
    dimensions = ["country", "indicator"]
    for optional in ("sub_indicator", "sex"):
        if optional in dataframe.columns:
            dimensions.append(optional)

    for keys, group in dataframe.groupby(dimensions, dropna=False):
        group = group.sort_values("year").dropna(subset=["value"])
        if len(group) < 4:
            continue

        changes = group["value"].diff()
        valid_changes = changes.dropna()
        standard_deviation = float(valid_changes.std(ddof=0))
        if not np.isfinite(standard_deviation) or standard_deviation == 0:
            continue
        mean_change = float(valid_changes.mean())

        for index in group.index[1:]:
            change = float(changes.loc[index])
            z_score = abs((change - mean_change) / standard_deviation)
            if z_score < z_threshold:
                continue

            row = group.loc[index]
            previous = group.loc[group.index[group.index.get_loc(index) - 1]]
            previous_value = float(previous["value"])
            percent_change = None if previous_value == 0 else (change / abs(previous_value)) * 100
            severity = "high" if z_score >= z_threshold + 1 else "moderate"
            anomalies.append(
                {
                    "country": row["country"],
                    "indicator": row["indicator"],
                    "year": int(row["year"]),
                    "value": round(float(row["value"]), 3),
                    "previous_value": round(previous_value, 3),
                    "absolute_change": round(change, 3),
                    "percentage_change": (
                        round(float(percent_change), 2) if percent_change is not None else None
                    ),
                    "z_score": round(z_score, 2),
                    "severity": severity,
                    "reason": "unusual year-over-year movement versus the historical series",
                }
            )

    anomalies = sorted(anomalies, key=lambda item: item["z_score"], reverse=True)[:limit]
    return {
        "count": len(anomalies),
        "method": "z-score on year-over-year changes",
        "threshold": z_threshold,
        "data": anomalies,
    }
