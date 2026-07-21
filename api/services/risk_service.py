from __future__ import annotations

from typing import Any

import pandas as pd

from api.repositories.health_repository import HealthRepository, repository

HIGHER_IS_WORSE = {
    "crude_death_ratio",
    "death_by_hiv_aids",
    "hiv_prevalence",
    "infant_mortality_rate",
    "malaria_prevalence",
    "maternal_mortality_rate",
    "tb_prevalence",
    "under_5_mortality_rate",
    "undernourished_population",
    "underweight_children",
}
LOWER_IS_WORSE = {
    "government_expenditure_in_health",
    "immunization_dpt",
    "immunization_measless",
    "life_expentancy_rate",
    "nurses_midwife_density",
    "pharmaceutical_worker_density",
    "physicans_density",
}


def _risk_level(score: float) -> str:
    if score < 34:
        return "low"
    if score < 67:
        return "moderate"
    return "high"


def country_risk_score(
    country: str,
    repo: HealthRepository = repository,
) -> dict[str, Any]:
    resolved = repo.resolve_country(country)
    latest = repo.latest_country_values(resolved)
    components: list[dict[str, Any]] = []

    for indicator in sorted(HIGHER_IS_WORSE | LOWER_IS_WORSE):
        country_rows = latest[latest["indicator"] == indicator]
        if country_rows.empty:
            continue

        peers = repo.latest_indicator_by_country(indicator)
        peers = peers.dropna(subset=["value"])
        if peers.empty:
            continue

        value = float(country_rows["value"].mean())
        minimum = float(peers["value"].min())
        maximum = float(peers["value"].max())
        if maximum == minimum:
            normalized = 0.5
        else:
            normalized = (value - minimum) / (maximum - minimum)
        if indicator in LOWER_IS_WORSE:
            normalized = 1 - normalized

        component_score = max(0.0, min(100.0, normalized * 100))
        components.append(
            {
                "indicator": indicator,
                "latest_value": round(value, 3),
                "risk_contribution": round(component_score, 2),
            }
        )

    score = round(
        sum(component["risk_contribution"] for component in components)
        / len(components),
        2,
    ) if components else 0.0
    drivers = sorted(
        components,
        key=lambda component: component["risk_contribution"],
        reverse=True,
    )[:3]

    return {
        "country": resolved,
        "risk_score": score,
        "risk_level": _risk_level(score),
        "indicators_used": len(components),
        "main_drivers": drivers,
        "method": "latest-value peer normalization across ASEAN countries",
        "is_ai_prediction": False,
        "disclaimer": (
            "Decision-support signal only; it is not a clinical diagnosis or a "
            "replacement for public-health judgement."
        ),
    }
