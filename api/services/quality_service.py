from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from api.repositories.health_repository import HealthRepository, repository


def data_quality_report(repo: HealthRepository = repository) -> dict[str, Any]:
    dataframe = repo.load_health_data()
    key_columns = ["country", "year", "indicator", "sub_indicator", "sex"]
    key_columns = [column for column in key_columns if column in dataframe.columns]
    duplicates = int(dataframe.duplicated(subset=key_columns, keep=False).sum())
    missing = {column: int(dataframe[column].isna().sum()) for column in dataframe.columns}
    required_missing = sum(missing.get(column, 0) for column in ["country", "year", "indicator", "value"])

    status = "pass" if required_missing == 0 and duplicates == 0 else "warning"
    return {
        "status": status,
        "record_count": int(len(dataframe)),
        "country_count": int(dataframe["country"].nunique()),
        "indicator_count": int(dataframe["indicator"].nunique()),
        "year_range": {
            "minimum": int(dataframe["year"].min()),
            "maximum": int(dataframe["year"].max()),
        },
        "duplicate_records": duplicates,
        "missing_values": missing,
        "required_field_failures": int(required_missing),
        "source_file": str(repo.health_path),
        "source_modified_at": datetime.fromtimestamp(
            repo.health_path.stat().st_mtime,
            tz=timezone.utc,
        ).isoformat(),
    }


def pipeline_status(repo: HealthRepository = repository) -> dict[str, Any]:
    quality = data_quality_report(repo)
    return {
        "status": "healthy" if quality["record_count"] > 0 else "degraded",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "batch_pipeline": {
            "status": "ready",
            "record_count": quality["record_count"],
            "quality_status": quality["status"],
            "latest_data_year": quality["year_range"]["maximum"],
        },
        "streaming_pipeline": {
            "status": "not_configured",
            "message": "Weather streaming is available as a separate resilience demo.",
        },
    }


def readiness(repo: HealthRepository = repository) -> dict[str, Any]:
    quality = data_quality_report(repo)
    checks = {
        "processed_data_available": quality["record_count"] > 0,
        "required_fields_valid": quality["required_field_failures"] == 0,
        "duplicates_absent": quality["duplicate_records"] == 0,
        "countries_available": quality["country_count"] > 0,
        "indicators_available": quality["indicator_count"] > 0,
    }
    return {
        "status": "ready" if all(checks.values()) else "not_ready",
        "checks": checks,
    }
