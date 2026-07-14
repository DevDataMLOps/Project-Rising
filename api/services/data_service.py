import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HEALTH_DATASET = (
    PROJECT_ROOT / "data" / "processed" / "asean_health_indicators.csv"
)


def get_health_indicators(
    country: str | None = None,
    indicator: str | None = None,
    year: int | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Read and filter processed ASEAN health indicators."""

    if not HEALTH_DATASET.exists():
        raise FileNotFoundError(
            f"Processed health dataset not found: {HEALTH_DATASET}"
        )

    records: list[dict[str, Any]] = []

    with HEALTH_DATASET.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            row_country = row["country"].strip()
            row_indicator = row["indicator"].strip()
            row_year = int(row["year"])
            row_value = float(row["value"])

            if country and row_country.casefold() != country.strip().casefold():
                continue

            if (
                indicator
                and row_indicator.casefold()
                != indicator.strip().casefold()
            ):
                continue

            if year is not None and row_year != year:
                continue

            records.append(
                {
                    "country": row_country,
                    "year": row_year,
                    "indicator": row_indicator,
                    "value": row_value,
                }
            )

            if len(records) >= limit:
                break

    return records


def get_countries() -> list[str]:
    """Return the countries available in the processed dataset."""

    if not HEALTH_DATASET.exists():
        raise FileNotFoundError(
            f"Processed health dataset not found: {HEALTH_DATASET}"
        )

    countries: set[str] = set()

    with HEALTH_DATASET.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            country = row["country"].strip()

            if country:
                countries.add(country)

    return sorted(countries)


def get_indicators() -> list[str]:
    """Return the indicators available in the processed dataset."""

    if not HEALTH_DATASET.exists():
        raise FileNotFoundError(
            f"Processed health dataset not found: {HEALTH_DATASET}"
        )

    indicators: set[str] = set()

    with HEALTH_DATASET.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            indicator = row["indicator"].strip()

            if indicator:
                indicators.add(indicator)

    return sorted(indicators)

def get_pipeline_status() -> dict[str, Any]:
    """Return the current status of available pipeline outputs."""

    dataset_exists = HEALTH_DATASET.exists()
    record_count = 0
    size_bytes = 0
    last_modified: str | None = None

    if dataset_exists:
        with HEALTH_DATASET.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as csv_file:
            record_count = sum(1 for _ in csv.DictReader(csv_file))

        file_details = HEALTH_DATASET.stat()
        size_bytes = file_details.st_size
        last_modified = datetime.fromtimestamp(
            file_details.st_mtime,
            tz=timezone.utc,
        ).isoformat()

    overall_status = "healthy" if dataset_exists else "degraded"

    return {
        "status": overall_status,
        "batch_pipeline": {
            "status": "ready" if dataset_exists else "missing",
            "dataset": "data/processed/asean_health_indicators.csv",
            "record_count": record_count,
            "size_bytes": size_bytes,
            "last_modified_utc": last_modified,
        },
        "streaming_pipeline": {
            "status": "not_configured",
            "accepted_events": 0,
            "failed_events": 0,
            "checkpoint_count": 0,
            "message": (
                "No streaming output, DLQ, or checkpoint files "
                "were found in the current repository."
            ),
        },
    }

def get_country_risk(country: str) -> dict[str, Any]:
    """Calculate a transparent comparative health-risk score."""

    if not HEALTH_DATASET.exists():
        raise FileNotFoundError(
            f"Processed health dataset not found: {HEALTH_DATASET}"
        )

    available_countries = get_countries()
    canonical_country = next(
        (
            item
            for item in available_countries
            if item.casefold() == country.strip().casefold()
        ),
        None,
    )

    if canonical_country is None:
        raise KeyError(f"Country not found: {country}")

    risk_indicators = {
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

    latest_values: dict[
        str,
        dict[str, tuple[int, float]],
    ] = {}

    with HEALTH_DATASET.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            indicator = row["indicator"].strip()

            if indicator not in risk_indicators:
                continue

            row_country = row["country"].strip()
            row_year = int(row["year"])
            row_value = float(row["value"])

            country_values = latest_values.setdefault(
                indicator,
                {},
            )
            previous_value = country_values.get(row_country)

            if (
                previous_value is None
                or row_year > previous_value[0]
            ):
                country_values[row_country] = (
                    row_year,
                    row_value,
                )

    components: list[dict[str, Any]] = []

    for indicator in sorted(risk_indicators):
        country_values = latest_values.get(indicator, {})
        target_value = country_values.get(canonical_country)

        if target_value is None:
            continue

        all_values = [
            value
            for _, value in country_values.values()
        ]

        minimum = min(all_values)
        maximum = max(all_values)

        if maximum == minimum:
            continue

        year, value = target_value
        component_score = (
            (value - minimum)
            / (maximum - minimum)
            * 100
        )

        components.append(
            {
                "indicator": indicator,
                "year": year,
                "value": value,
                "comparative_score": round(
                    component_score,
                    1,
                ),
            }
        )

    if not components:
        raise ValueError(
            f"No risk indicators are available for {canonical_country}"
        )

    risk_score = sum(
        component["comparative_score"]
        for component in components
    ) / len(components)

    if risk_score < 33.3:
        risk_level = "low"
    elif risk_score < 66.7:
        risk_level = "moderate"
    else:
        risk_level = "high"

    return {
        "country": canonical_country,
        "risk_score": round(risk_score, 1),
        "risk_level": risk_level,
        "indicators_used": len(components),
        "components": components,
        "is_ai_prediction": False,
        "methodology": (
            "Latest available risk indicators are normalized "
            "against other countries in the current dataset, "
            "then averaged into a comparative score from 0 to 100."
        ),
        "disclaimer": (
            "This is a transparent MVP demonstration score, "
            "not a clinical assessment or predictive AI model."
        ),
    }