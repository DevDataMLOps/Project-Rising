from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HEALTH_DATASET = (
    PROJECT_ROOT / "data" / "processed" / "asean_health_indicators.csv"
)

SUPPORTED_DISEASES = {
    "dengue": "Dengue",
    "malaria": "Malaria",
    "mosquito_borne": "Mosquito-borne disease",
}

HEALTH_INDICATOR_WEIGHTS = {
    "malaria_prevalence": 0.7,
    "infant_mortality_rate": 0.3,
}


def _latest_indicator_values() -> dict[str, dict[str, tuple[int, float]]]:
    if not HEALTH_DATASET.exists():
        raise FileNotFoundError(
            f"Processed health dataset not found: {HEALTH_DATASET}"
        )

    latest: dict[str, dict[str, tuple[int, float]]] = {}
    with HEALTH_DATASET.open(encoding="utf-8-sig", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            indicator = row["indicator"].strip()
            if indicator not in HEALTH_INDICATOR_WEIGHTS:
                continue

            country = row["country"].strip()
            year = int(row["year"])
            value = float(row["value"])
            country_values = latest.setdefault(indicator, {})
            previous = country_values.get(country)
            if previous is None or year > previous[0]:
                country_values[country] = (year, value)

    return latest


def _canonical_country(
    country: str,
    values: dict[str, dict[str, tuple[int, float]]],
) -> str:
    countries = {
        item
        for indicator_values in values.values()
        for item in indicator_values
    }
    canonical = next(
        (item for item in countries if item.casefold() == country.strip().casefold()),
        None,
    )
    if canonical is None:
        raise KeyError(f"Country not found: {country}")
    return canonical


def _health_vulnerability(
    country: str,
    values: dict[str, dict[str, tuple[int, float]]],
) -> tuple[float, list[dict[str, Any]]]:
    components: list[dict[str, Any]] = []
    weighted_score = 0.0
    available_weight = 0.0

    for indicator, weight in HEALTH_INDICATOR_WEIGHTS.items():
        country_values = values.get(indicator, {})
        target = country_values.get(country)
        if target is None or not country_values:
            continue

        all_values = [value for _, value in country_values.values()]
        minimum = min(all_values)
        maximum = max(all_values)
        year, value = target
        normalized = (
            0.5 if maximum == minimum else (value - minimum) / (maximum - minimum)
        )
        weighted_score += normalized * weight
        available_weight += weight
        components.append(
            {
                "indicator": indicator,
                "year": year,
                "value": value,
                "normalized_vulnerability": round(normalized, 3),
            }
        )

    if not components:
        raise ValueError(f"No health-risk indicators are available for {country}")

    return weighted_score / available_weight, components


def _risk_level(score: float) -> str:
    if score < 35:
        return "low"
    if score < 65:
        return "moderate"
    return "high"


def predict_disease_risk(
    *,
    country: str,
    temperature_c: float,
    rainfall_mm: float,
    humidity_pct: float,
    disease: str = "mosquito_borne",
) -> dict[str, Any]:
    """Estimate near-term mosquito-borne disease risk with explainable inputs.

    This is a transparent hackathon decision-support model. It is deliberately
    deterministic and is not a clinically validated outbreak forecast.
    """

    disease_key = disease.strip().casefold().replace("-", "_").replace(" ", "_")
    if disease_key not in SUPPORTED_DISEASES:
        raise ValueError(
            f"Unsupported disease '{disease}'. Choose one of: "
            f"{', '.join(sorted(SUPPORTED_DISEASES))}"
        )

    values = _latest_indicator_values()
    canonical_country = _canonical_country(country, values)
    health_score, health_components = _health_vulnerability(
        canonical_country,
        values,
    )

    temperature_suitability = max(0.0, 1.0 - abs(temperature_c - 28.0) / 12.0)
    rainfall_pressure = min(max(rainfall_mm / 200.0, 0.0), 1.0)
    humidity_pressure = min(max((humidity_pct - 50.0) / 40.0, 0.0), 1.0)
    climate_score = (
        0.35 * temperature_suitability
        + 0.40 * rainfall_pressure
        + 0.25 * humidity_pressure
    )

    score = round((0.70 * climate_score + 0.30 * health_score) * 100, 1)
    level = _risk_level(score)
    recommendations = {
        "low": [
            "Maintain routine vector and symptom surveillance.",
            "Refresh the forecast when weather conditions change.",
        ],
        "moderate": [
            "Increase mosquito and syndromic surveillance in exposed areas.",
            "Verify diagnostic supplies and community messaging readiness.",
        ],
        "high": [
            "Escalate vector-control and case-surveillance activities.",
            "Pre-position diagnostics, treatment supplies, and response staff.",
        ],
    }

    return {
        "country": canonical_country,
        "disease": SUPPORTED_DISEASES[disease_key],
        "forecast_window": "next 14 days",
        "risk_score": score,
        "risk_probability": round(score / 100, 3),
        "risk_level": level,
        "model": {
            "name": "RISING Explainable Climate-Health Risk Model",
            "version": "1.0.0",
            "type": "deterministic statistical scoring model",
        },
        "climate_inputs": {
            "temperature_c": temperature_c,
            "rainfall_mm": rainfall_mm,
            "humidity_pct": humidity_pct,
        },
        "score_breakdown": {
            "climate_suitability": round(climate_score * 100, 1),
            "historical_health_vulnerability": round(health_score * 100, 1),
            "weights": {"climate": 0.70, "health": 0.30},
        },
        "health_evidence": health_components,
        "recommendations": recommendations[level],
        "disclaimer": (
            "Hackathon decision-support estimate only; it is not a clinical "
            "diagnosis, an epidemiological forecast, or a substitute for local "
            "public-health surveillance."
        ),
    }
