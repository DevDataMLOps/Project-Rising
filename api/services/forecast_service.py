"""Transparent historical trend forecasting for Phase 4."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HEALTH_DATASET = PROJECT_ROOT / "data" / "processed" / "asean_health_indicators.csv"

HIGHER_IS_WORSE = {
    "crude_death_ratio",
    "hiv_prevalence",
    "infant_mortality_rate",
    "malaria_prevalence",
    "maternal_mortality_rate",
    "tb_prevalence",
    "under_5_mortality_rate",
    "undernourishment_rate",
    "underweight_children",
}
LOWER_IS_WORSE = {
    "immunization_dpt",
    "immunization_measles",
    "life_expectancy_rate",
}


def _load_series(country: str, indicator: str) -> tuple[str, str, list[tuple[int, float]]]:
    if not HEALTH_DATASET.exists():
        raise FileNotFoundError(f"Processed health dataset not found: {HEALTH_DATASET}")

    values: dict[int, list[float]] = defaultdict(list)
    canonical_country: str | None = None
    canonical_indicator: str | None = None
    with HEALTH_DATASET.open("r", encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            row_country = row.get("country", "").strip()
            row_indicator = row.get("indicator", "").strip()
            if row_country.casefold() != country.strip().casefold():
                continue
            if row_indicator.casefold() != indicator.strip().casefold():
                continue
            try:
                year = int(float(row["year"]))
                value = float(row["value"])
            except (KeyError, TypeError, ValueError):
                continue
            if not np.isfinite(value):
                continue
            canonical_country = row_country
            canonical_indicator = row_indicator
            values[year].append(value)

    if canonical_country is None:
        raise KeyError(f"No data found for country={country!r}, indicator={indicator!r}")

    series = sorted(
        (year, float(np.mean(year_values)))
        for year, year_values in values.items()
        if year_values
    )
    if len(series) < 2:
        raise ValueError("At least two historical years are required for forecasting")
    return canonical_country, canonical_indicator or indicator, series


def _direction(indicator: str, slope: float) -> tuple[str, str]:
    tolerance = 1e-9
    if abs(slope) <= tolerance:
        return "stable", "neutral"
    trend = "increasing" if slope > 0 else "decreasing"
    if indicator in HIGHER_IS_WORSE:
        implication = "worsening" if slope > 0 else "improving"
    elif indicator in LOWER_IS_WORSE:
        implication = "improving" if slope > 0 else "worsening"
    else:
        implication = "requires_context"
    return trend, implication


def forecast_health_indicator(
    country: str,
    indicator: str,
    *,
    horizon_years: int = 3,
) -> dict[str, Any]:
    """Fit a simple linear trend and forecast future annual values."""

    if not 1 <= horizon_years <= 5:
        raise ValueError("horizon_years must be between 1 and 5")

    canonical_country, canonical_indicator, series = _load_series(country, indicator)
    years = np.array([year for year, _ in series], dtype=float)
    values = np.array([value for _, value in series], dtype=float)
    slope, intercept = np.polyfit(years, values, 1)
    fitted = slope * years + intercept
    residual_sum = float(np.sum((values - fitted) ** 2))
    total_sum = float(np.sum((values - np.mean(values)) ** 2))
    r_squared = 1.0 if total_sum == 0 else max(0.0, 1.0 - residual_sum / total_sum)

    last_year = int(years.max())
    forecasts = []
    for offset in range(1, horizon_years + 1):
        target_year = last_year + offset
        predicted = float(slope * target_year + intercept)
        forecasts.append({"year": target_year, "predicted_value": round(predicted, 3)})

    trend, implication = _direction(canonical_indicator, float(slope))
    confidence = "high" if len(series) >= 8 and r_squared >= 0.75 else "moderate"
    if len(series) < 5 or r_squared < 0.35:
        confidence = "low"

    return {
        "country": canonical_country,
        "indicator": canonical_indicator,
        "historical": [
            {"year": year, "value": round(value, 3)} for year, value in series
        ],
        "forecast": forecasts,
        "trend": trend,
        "public_health_implication": implication,
        "annual_slope": round(float(slope), 6),
        "r_squared": round(r_squared, 4),
        "confidence": confidence,
        "model": {
            "name": "RISING Historical Linear Trend",
            "version": "1.0.0",
            "type": "ordinary least-squares trend extrapolation",
            "is_clinically_validated": False,
        },
        "limitations": [
            "Uses historical indicator values only and does not model causal drivers.",
            "Should support preparedness planning, not diagnosis or clinical decisions.",
            "Live weather and verified outbreak labels are future production inputs.",
        ],
    }
