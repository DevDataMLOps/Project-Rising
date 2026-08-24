"""Train the Phase 4B unsupervised anomaly-detection model."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from ml.data import dataset_sha256, load_health_data
from ml.features import ANOMALY_FEATURES, build_anomaly_frame

ANOMALY_ARTIFACT = "anomaly_model.joblib"


def _version(dataset_hash: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"anomaly-iforest-{dataset_hash[:8]}-{stamp}"


def train_anomaly_model(data_path: Path, model_directory: Path) -> dict[str, Any]:
    """Train, summarize, version, and persist an Isolation Forest model."""
    data_path = Path(data_path)
    model_directory = Path(model_directory)
    model_directory.mkdir(parents=True, exist_ok=True)

    data = load_health_data(data_path)
    feature_frame, baseline = build_anomaly_frame(data)
    matrix = feature_frame[ANOMALY_FEATURES].to_numpy(dtype=float)

    model = IsolationForest(
        n_estimators=260,
        contamination=0.03,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(matrix)
    labels = model.predict(matrix)
    raw_anomaly = -model.decision_function(matrix)
    q05 = float(np.quantile(raw_anomaly, 0.05))
    q50 = float(np.quantile(raw_anomaly, 0.50))
    q95 = float(np.quantile(raw_anomaly, 0.95))
    if q95 <= q05:
        q95 = q05 + 1.0

    data_hash = dataset_sha256(data_path)
    trained_at = datetime.now(timezone.utc).isoformat()
    artifact: dict[str, Any] = {
        "kind": "health_indicator_anomaly_detection",
        "version": _version(data_hash),
        "trained_at": trained_at,
        "dataset_path": str(data_path),
        "dataset_sha256": data_hash,
        "model": model,
        "feature_columns": ANOMALY_FEATURES,
        "countries": sorted(data["country"].unique().tolist()),
        "indicators": sorted(data["indicator"].unique().tolist()),
        "baseline": baseline,
        "score_calibration": {"q05": q05, "q50": q50, "q95": q95},
        "metrics": {
            "training_rows": int(len(feature_frame)),
            "contamination": 0.03,
            "flagged_rows": int((labels == -1).sum()),
            "flagged_rate": round(float((labels == -1).mean()), 6),
            "mean_decision_function": round(
                float(model.decision_function(matrix).mean()), 6
            ),
            "evaluation_note": (
                "Unsupervised model: no labeled outbreak or anomaly ground truth is available."
            ),
        },
        "responsible_use": (
            "Anomaly flags identify statistically unusual aggregate records for review. "
            "They do not establish data corruption, disease outbreaks, or clinical risk."
        ),
    }
    artifact_path = model_directory / ANOMALY_ARTIFACT
    joblib.dump(artifact, artifact_path)

    return {
        "kind": artifact["kind"],
        "version": artifact["version"],
        "trained_at": trained_at,
        "artifact": str(artifact_path),
        "dataset_sha256": data_hash,
        "metrics": artifact["metrics"],
    }
