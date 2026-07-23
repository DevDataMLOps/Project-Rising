"""Inference, model metadata, and drift monitoring for Phase 4B."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ml.config import health_data_path, model_dir
from ml.data import canonical_value, dataset_sha256, load_health_data, series_key
from ml.features import (
    FORECAST_CATEGORICAL_FEATURES,
    FORECAST_NUMERIC_FEATURES,
    anomaly_feature_vector,
)
from ml.registry import load_registry, load_training_report
from ml.train_anomaly import ANOMALY_ARTIFACT
from ml.train_forecast import FORECAST_ARTIFACT


class MLService:
    """Load trained artifacts and expose responsible aggregate-health inference."""

    def __init__(
        self,
        model_directory: Path | None = None,
        data_path: Path | None = None,
    ) -> None:
        self.model_directory = Path(model_directory or model_dir()).resolve()
        self.data_path = Path(data_path or health_data_path()).resolve()

    @property
    def forecast_path(self) -> Path:
        return self.model_directory / FORECAST_ARTIFACT

    @property
    def anomaly_path(self) -> Path:
        return self.model_directory / ANOMALY_ARTIFACT

    def readiness(self) -> dict[str, Any]:
        files = {
            "forecast_model": self.forecast_path.exists(),
            "anomaly_model": self.anomaly_path.exists(),
            "registry": (self.model_directory / "registry.json").exists(),
            "training_report": (self.model_directory / "training_report.json").exists(),
            "processed_dataset": self.data_path.exists(),
        }
        ready = all(files.values())
        return {
            "status": "ready" if ready else "training_required",
            "phase": "4B",
            "artifacts": files,
            "training_command": "python -m ml.train_all",
            "capabilities": {
                "trained_health_indicator_forecasting": files["forecast_model"],
                "trained_unsupervised_anomaly_detection": files["anomaly_model"],
                "model_version_registry": files["registry"],
                "drift_monitoring": files["registry"] and files["processed_dataset"],
                "patient_level_prediction": False,
                "clinically_validated_outbreak_forecast": False,
            },
            "responsible_use": (
                "Phase 4B operates on aggregated annual public-health indicators. "
                "Outputs require human public-health review and are not clinical advice."
            ),
        }

    def registry(self) -> dict[str, Any]:
        return load_registry(self.model_directory)

    def training_report(self) -> dict[str, Any]:
        return load_training_report(self.model_directory)

    def _load_forecast(self) -> dict[str, Any]:
        if not self.forecast_path.exists():
            raise FileNotFoundError(
                f"Forecast model not trained: {self.forecast_path}. "
                "Run: python -m ml.train_all"
            )
        return joblib.load(self.forecast_path)

    def _load_anomaly(self) -> dict[str, Any]:
        if not self.anomaly_path.exists():
            raise FileNotFoundError(
                f"Anomaly model not trained: {self.anomaly_path}. "
                "Run: python -m ml.train_all"
            )
        return joblib.load(self.anomaly_path)

    def forecast(
        self,
        country: str,
        indicator: str,
        horizon_years: int,
    ) -> dict[str, Any]:
        artifact = self._load_forecast()
        canonical_country = canonical_value(country, artifact["countries"], "country")
        canonical_indicator = canonical_value(
            indicator, artifact["indicators"], "indicator"
        )
        key = series_key(canonical_country, canonical_indicator)
        history = artifact["histories"].get(key, [])
        if len(history) < 2:
            raise ValueError(
                f"At least two historical values are required for {canonical_country} / "
                f"{canonical_indicator}."
            )

        pipeline = artifact["pipeline"]
        preprocessor = pipeline.named_steps["preprocessor"]
        forest = pipeline.named_steps["model"]
        recent = [dict(item) for item in history]
        predictions: list[dict[str, Any]] = []

        for _ in range(horizon_years):
            next_year = int(recent[-1]["year"]) + 1
            values = [float(item["value"]) for item in recent]
            lag1 = values[-1]
            lag2 = values[-2]
            rolling_values = values[-3:]
            record = pd.DataFrame(
                [
                    {
                        "country": canonical_country,
                        "indicator": canonical_indicator,
                        "year": next_year,
                        "lag1": lag1,
                        "lag2": lag2,
                        "rolling_mean_3": float(np.mean(rolling_values)),
                        "rolling_std_3": float(np.std(rolling_values, ddof=0)),
                        "trend_delta": lag1 - lag2,
                    }
                ]
            )
            feature_columns = FORECAST_CATEGORICAL_FEATURES + FORECAST_NUMERIC_FEATURES
            indicator_range = artifact["indicator_ranges"][canonical_indicator]
            plausible_min = max(
                0.0,
                float(indicator_range["minimum"]) - 3.0 * float(indicator_range["std"]),
            )
            plausible_max = float(indicator_range["maximum"]) + 3.0 * float(
                indicator_range["std"]
            )
            predicted = float(pipeline.predict(record[feature_columns])[0])
            predicted = float(np.clip(predicted, plausible_min, plausible_max))
            transformed = preprocessor.transform(record[feature_columns])
            tree_predictions = np.array(
                [tree.predict(transformed)[0] for tree in forest.estimators_], dtype=float
            )
            tree_predictions = np.clip(tree_predictions, plausible_min, plausible_max)
            residual_std = float(
                artifact.get("residual_std_by_indicator", {}).get(
                    canonical_indicator, 0.0
                )
            )
            lower = max(
                plausible_min,
                float(np.quantile(tree_predictions, 0.10) - residual_std * 0.25),
            )
            upper = min(
                plausible_max,
                max(
                    lower,
                    float(np.quantile(tree_predictions, 0.90) + residual_std * 0.25),
                ),
            )
            predictions.append(
                {
                    "year": next_year,
                    "predicted_value": round(predicted, 4),
                    "prediction_interval_80": {
                        "lower": round(lower, 4),
                        "upper": round(upper, 4),
                    },
                }
            )
            recent.append({"year": next_year, "value": predicted})
            recent = recent[-5:]

        recent_change = float(history[-1]["value"]) - float(history[-2]["value"])
        direction = "increasing" if recent_change > 0 else "decreasing" if recent_change < 0 else "stable"
        return {
            "country": canonical_country,
            "indicator": canonical_indicator,
            "historical_latest": history[-1],
            "horizon_years": horizon_years,
            "forecast": predictions,
            "recent_direction": direction,
            "model": {
                "name": "RISING Random Forest Health Indicator Forecaster",
                "version": artifact["version"],
                "trained_at": artifact["trained_at"],
                "type": "supervised random forest regression",
                "dataset_sha256": artifact["dataset_sha256"],
                "holdout_metrics": {
                    key: value
                    for key, value in artifact["metrics"].items()
                    if key != "per_indicator"
                },
                "indicator_holdout_metrics": artifact["metrics"]["per_indicator"].get(
                    canonical_indicator
                ),
            },
            "explainability": {
                "method": "global model feature importance plus recent lag values",
                "top_features": artifact.get("feature_importance", [])[:8],
                "lag1": round(float(history[-1]["value"]), 4),
                "lag2": round(float(history[-2]["value"]), 4),
            },
            "is_ml_prediction": True,
            "disclaimer": artifact["responsible_use"],
        }

    def anomaly_prediction(
        self,
        *,
        country: str,
        indicator: str,
        year: int,
        value: float,
        previous_value: float | None,
    ) -> dict[str, Any]:
        artifact = self._load_anomaly()
        canonical_country = canonical_value(country, artifact["countries"], "country")
        canonical_indicator = canonical_value(
            indicator, artifact["indicators"], "indicator"
        )
        baseline = artifact["baseline"]
        latest = baseline["latest_values"].get(
            series_key(canonical_country, canonical_indicator)
        )
        effective_previous = previous_value
        previous_source = "request"
        if effective_previous is None and latest is not None:
            effective_previous = float(latest["value"])
            previous_source = "training_baseline"

        vector, readable = anomaly_feature_vector(
            indicator=canonical_indicator,
            year=year,
            value=value,
            previous_value=effective_previous,
            baseline=baseline,
        )
        model = artifact["model"]
        label = int(model.predict(vector)[0])
        decision = float(model.decision_function(vector)[0])
        raw_anomaly = -decision
        calibration = artifact["score_calibration"]
        denominator = max(float(calibration["q95"]) - float(calibration["q05"]), 1e-9)
        score = float(
            np.clip(
                (raw_anomaly - float(calibration["q05"])) / denominator * 100.0,
                0.0,
                100.0,
            )
        )
        is_anomaly = label == -1
        review_level = "high" if is_anomaly or score >= 75 else "review" if score >= 45 else "low"
        evidence = [
            f"Value is {abs(readable['value_zscore']):.2f} standard deviations from the indicator mean.",
            f"Year-over-year change is {abs(readable['delta_zscore']):.2f} standard deviations from its usual change.",
        ]
        return {
            "country": canonical_country,
            "indicator": canonical_indicator,
            "year": int(year),
            "value": float(value),
            "previous_value": effective_previous,
            "previous_value_source": previous_source,
            "is_anomaly": is_anomaly,
            "anomaly_score": round(score, 2),
            "review_level": review_level,
            "decision_function": round(decision, 6),
            "engineered_features": {
                key: round(float(value), 6) for key, value in readable.items()
            },
            "evidence": evidence,
            "recommended_action": (
                "Review source lineage, units, transformation logs, and neighboring years "
                "before accepting or rejecting the record."
            ),
            "model": {
                "name": "RISING Isolation Forest Health Anomaly Detector",
                "version": artifact["version"],
                "trained_at": artifact["trained_at"],
                "type": "unsupervised isolation forest",
                "training_metrics": artifact["metrics"],
            },
            "is_ml_prediction": True,
            "disclaimer": artifact["responsible_use"],
        }

    def drift_report(self) -> dict[str, Any]:
        registry = self.registry()
        anomaly = self._load_anomaly()
        current = load_health_data(self.data_path)
        baseline = anomaly["baseline"]["indicator_baseline"]

        details: list[dict[str, Any]] = []
        for indicator, group in current.groupby("indicator"):
            indicator = str(indicator)
            current_mean = float(group["value"].mean())
            current_count = int(len(group))
            current_latest_year = int(group["year"].max())
            reference = baseline.get(indicator)
            if reference is None:
                details.append(
                    {
                        "indicator": indicator,
                        "status": "new_indicator",
                        "standardized_mean_shift": None,
                        "current_count": current_count,
                    }
                )
                continue
            shift = abs(current_mean - float(reference["mean"])) / max(
                float(reference["std"]), 1e-9
            )
            status = "drift" if shift >= 1.0 else "watch" if shift >= 0.5 else "stable"
            details.append(
                {
                    "indicator": indicator,
                    "status": status,
                    "standardized_mean_shift": round(float(shift), 4),
                    "baseline_count": int(reference["count"]),
                    "current_count": current_count,
                    "baseline_latest_year": int(reference["latest_year"]),
                    "current_latest_year": current_latest_year,
                }
            )

        drift_count = sum(item["status"] in {"drift", "new_indicator"} for item in details)
        watch_count = sum(item["status"] == "watch" for item in details)
        overall = "drift" if drift_count else "watch" if watch_count else "stable"
        current_hash = dataset_sha256(self.data_path)
        return {
            "status": overall,
            "dataset_changed_since_training": current_hash != registry["dataset"]["sha256"],
            "training_dataset_sha256": registry["dataset"]["sha256"],
            "current_dataset_sha256": current_hash,
            "drifted_indicators": drift_count,
            "watched_indicators": watch_count,
            "details": sorted(
                details,
                key=lambda item: (
                    item.get("standardized_mean_shift") is not None,
                    item.get("standardized_mean_shift") or 0,
                ),
                reverse=True,
            ),
            "method": (
                "Standardized indicator-mean shift versus the training baseline. "
                "Thresholds: watch >= 0.5 standard deviations; drift >= 1.0."
            ),
            "retraining_command": "python -m ml.train_all",
        }
