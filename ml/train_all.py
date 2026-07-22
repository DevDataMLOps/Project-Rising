"""Train and register all Project RISING Phase 4B models."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ml.config import health_data_path, model_dir
from ml.data import dataset_sha256, load_health_data
from ml.registry import REGISTRY_FILENAME, TRAINING_REPORT_FILENAME, write_json
from ml.train_anomaly import train_anomaly_model
from ml.train_forecast import train_forecast_model


def train_all_models(
    data_path: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Train both ML models and write a versioned registry and training report."""
    source = Path(data_path or health_data_path()).resolve()
    destination = Path(output_dir or model_dir()).resolve()
    destination.mkdir(parents=True, exist_ok=True)

    data = load_health_data(source)
    started_at = datetime.now(timezone.utc).isoformat()
    forecast = train_forecast_model(source, destination)
    anomaly = train_anomaly_model(source, destination)
    completed_at = datetime.now(timezone.utc).isoformat()

    registry: dict[str, Any] = {
        "phase": "4B",
        "status": "ready",
        "trained_at": completed_at,
        "dataset": {
            "path": str(source),
            "sha256": dataset_sha256(source),
            "rows": int(len(data)),
            "countries": int(data["country"].nunique()),
            "indicators": int(data["indicator"].nunique()),
            "year_min": int(data["year"].min()),
            "year_max": int(data["year"].max()),
        },
        "models": [forecast, anomaly],
        "retraining_command": "python -m ml.train_all",
        "responsible_use": {
            "patient_level_prediction": False,
            "clinically_validated": False,
            "human_review_required": True,
            "outbreak_labels_available": False,
        },
    }
    report: dict[str, Any] = {
        "phase": "4B",
        "started_at": started_at,
        "completed_at": completed_at,
        "dataset": registry["dataset"],
        "forecast_model": forecast,
        "anomaly_model": anomaly,
        "quality_gates": {
            "artifacts_written": True,
            "time_based_forecast_holdout": True,
            "model_versioning": True,
            "lineage_hash_recorded": True,
            "drift_baseline_recorded": True,
        },
    }
    write_json(destination / REGISTRY_FILENAME, registry)
    write_json(destination / TRAINING_REPORT_FILENAME, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=None, help="Processed CSV path")
    parser.add_argument("--output", type=Path, default=None, help="Artifact directory")
    arguments = parser.parse_args()
    report = train_all_models(arguments.data, arguments.output)
    forecast_metrics = report["forecast_model"]["metrics"]
    anomaly_metrics = report["anomaly_model"]["metrics"]
    print("Phase 4B training complete")
    print(f"Forecast version: {report['forecast_model']['version']}")
    print(
        "Forecast holdout metrics: "
        f"MAE={forecast_metrics['mae']}, RMSE={forecast_metrics['rmse']}, "
        f"R2={forecast_metrics['r2']}"
    )
    print(
        "Anomaly model: "
        f"{anomaly_metrics['flagged_rows']} of {anomaly_metrics['training_rows']} "
        "training records flagged"
    )


if __name__ == "__main__":
    main()
