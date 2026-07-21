from __future__ import annotations

from typing import Any

from api.repositories.health_repository import HealthRepository, repository
from api.services.risk_service import country_risk_score

SUPPORTED_DISEASES = {"dengue": "Dengue", "malaria": "Malaria"}


def _level(probability: float) -> str:
    if probability < 0.34:
        return "low"
    if probability < 0.67:
        return "moderate"
    return "high"


def _weather_risk(
    disease: str,
    temperature_c: float,
    rainfall_mm: float,
    humidity_pct: float,
) -> tuple[float, list[str]]:
    evidence: list[str] = []

    if disease == "dengue":
        temperature = max(0.0, 1 - abs(temperature_c - 29.0) / 12.0)
        rainfall = min(rainfall_mm / 200.0, 1.0)
        humidity = min(max((humidity_pct - 45.0) / 45.0, 0.0), 1.0)
    else:
        temperature = max(0.0, 1 - abs(temperature_c - 27.0) / 13.0)
        rainfall = min(rainfall_mm / 160.0, 1.0)
        humidity = min(max((humidity_pct - 40.0) / 50.0, 0.0), 1.0)

    if temperature >= 0.7:
        evidence.append("temperature is favorable for mosquito activity")
    if rainfall >= 0.65:
        evidence.append("high rainfall may increase mosquito breeding habitat")
    if humidity >= 0.65:
        evidence.append("high humidity may support mosquito survival")

    return (0.4 * temperature) + (0.35 * rainfall) + (0.25 * humidity), evidence


def predict_disease_risk(
    *,
    country: str,
    disease: str,
    temperature_c: float,
    rainfall_mm: float,
    humidity_pct: float,
    repo: HealthRepository = repository,
) -> dict[str, Any]:
    resolved_country = repo.resolve_country(country)
    normalized_disease = disease.strip().casefold()
    if normalized_disease not in SUPPORTED_DISEASES:
        raise KeyError(disease)
    if rainfall_mm < 0 or not 0 <= humidity_pct <= 100:
        raise ValueError("Weather inputs are outside valid ranges.")

    weather_score, weather_evidence = _weather_risk(
        normalized_disease,
        temperature_c,
        rainfall_mm,
        humidity_pct,
    )
    baseline = country_risk_score(resolved_country, repo)
    baseline_score = baseline["risk_score"] / 100
    probability = max(0.0, min(1.0, (0.70 * weather_score) + (0.30 * baseline_score)))
    risk_score = round(probability * 100, 2)

    health_evidence = [
        {
            "indicator": driver["indicator"],
            "value": driver["latest_value"],
            "risk_contribution": driver["risk_contribution"],
        }
        for driver in baseline["main_drivers"]
    ]
    if not health_evidence:
        health_evidence = [{"indicator": "country_baseline", "value": baseline_score}]

    risk_level = _level(probability)
    recommendations = [
        "Strengthen vector surveillance and remove standing-water breeding sites.",
        (
            "Prepare targeted public-health messaging and clinical readiness."
            if risk_level != "low"
            else "Continue routine monitoring and prevention communication."
        ),
    ]

    return {
        "country": resolved_country,
        "disease": SUPPORTED_DISEASES[normalized_disease],
        "forecast_window": "next 14 days",
        "risk_probability": round(probability, 4),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "weather_evidence": weather_evidence,
        "health_evidence": health_evidence,
        "recommendations": recommendations,
        "model": {
            "name": "RISING Climate-Health Heuristic MVP",
            "version": "1.0.0",
            "type": "explainable weighted risk model",
            "is_ai_prediction": False,
        },
        "disclaimer": "Not a clinical diagnosis or an outbreak declaration.",
    }
