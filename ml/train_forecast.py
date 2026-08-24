"""Train the Phase 4B health-indicator forecasting model."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.data import dataset_sha256, load_health_data, series_key
from ml.features import (
    FORECAST_CATEGORICAL_FEATURES,
    FORECAST_NUMERIC_FEATURES,
    build_forecast_frame,
    time_holdout_split,
)

FORECAST_ARTIFACT = "forecast_model.joblib"


def _version(dataset_hash: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"forecast-rf-{dataset_hash[:8]}-{stamp}"


def train_forecast_model(data_path: Path, model_directory: Path) -> dict[str, Any]:
    """Train, evaluate, version, and persist a global annual indicator forecaster."""
    data_path = Path(data_path)
    model_directory = Path(model_directory)
    model_directory.mkdir(parents=True, exist_ok=True)

    data = load_health_data(data_path)
    supervised = build_forecast_frame(data)
    train, test = time_holdout_split(supervised)

    feature_columns = FORECAST_CATEGORICAL_FEATURES + FORECAST_NUMERIC_FEATURES
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                FORECAST_CATEGORICAL_FEATURES,
            ),
            ("numeric", StandardScaler(), FORECAST_NUMERIC_FEATURES),
        ],
        remainder="drop",
    )
    regressor = RandomForestRegressor(
        n_estimators=240,
        max_depth=14,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    pipeline = Pipeline(
        steps=[("preprocessor", preprocessor), ("model", regressor)]
    )
    pipeline.fit(train[feature_columns], train["value"])

    predictions = pipeline.predict(test[feature_columns])
    mae = float(mean_absolute_error(test["value"], predictions))
    rmse = float(np.sqrt(mean_squared_error(test["value"], predictions)))
    r2 = float(r2_score(test["value"], predictions)) if len(test) > 1 else None
    smape_denominator = np.abs(test["value"].to_numpy()) + np.abs(predictions)
    smape = float(
        np.mean(
            np.where(
                smape_denominator > 1e-9,
                2.0 * np.abs(test["value"].to_numpy() - predictions)
                / smape_denominator,
                0.0,
            )
        )
        * 100.0
    )

    evaluation = test.loc[:, ["country", "indicator", "year", "value"]].copy()
    evaluation["prediction"] = predictions
    evaluation["residual"] = evaluation["value"] - evaluation["prediction"]
    per_indicator_metrics: dict[str, dict[str, float | int | None]] = {}
    residual_std_by_indicator: dict[str, float] = {}
    for indicator, group in evaluation.groupby("indicator"):
        group_predictions = group["prediction"].to_numpy(dtype=float)
        group_actual = group["value"].to_numpy(dtype=float)
        group_r2 = (
            float(r2_score(group_actual, group_predictions))
            if len(group) > 1
            else None
        )
        group_residual_std = float(np.std(group["residual"].to_numpy(), ddof=0))
        residual_std_by_indicator[str(indicator)] = group_residual_std
        per_indicator_metrics[str(indicator)] = {
            "mae": round(float(mean_absolute_error(group_actual, group_predictions)), 6),
            "rmse": round(
                float(np.sqrt(mean_squared_error(group_actual, group_predictions))), 6
            ),
            "r2": None if group_r2 is None else round(group_r2, 6),
            "residual_std": round(group_residual_std, 6),
            "test_rows": int(len(group)),
        }

    fitted_preprocessor = pipeline.named_steps["preprocessor"]
    names = fitted_preprocessor.get_feature_names_out()
    importances = pipeline.named_steps["model"].feature_importances_
    ranked = sorted(
        (
            {"feature": str(name), "importance": round(float(importance), 6)}
            for name, importance in zip(names, importances, strict=True)
        ),
        key=lambda item: item["importance"],
        reverse=True,
    )[:15]

    histories: dict[str, list[dict[str, float | int]]] = {}
    for (country, indicator), group in data.groupby(["country", "indicator"]):
        tail = group.sort_values("year").tail(5)
        histories[series_key(str(country), str(indicator))] = [
            {"year": int(row.year), "value": float(row.value)}
            for row in tail.itertuples(index=False)
        ]

    data_hash = dataset_sha256(data_path)
    trained_at = datetime.now(timezone.utc).isoformat()
    artifact: dict[str, Any] = {
        "kind": "health_indicator_forecast",
        "version": _version(data_hash),
        "trained_at": trained_at,
        "dataset_path": str(data_path),
        "dataset_sha256": data_hash,
        "pipeline": pipeline,
        "feature_columns": feature_columns,
        "countries": sorted(data["country"].unique().tolist()),
        "indicators": sorted(data["indicator"].unique().tolist()),
        "histories": histories,
        "training_year_min": int(data["year"].min()),
        "training_year_max": int(data["year"].max()),
        "residual_std_by_indicator": residual_std_by_indicator,
        "indicator_ranges": {
            str(indicator): {
                "minimum": float(group["value"].min()),
                "maximum": float(group["value"].max()),
                "std": float(group["value"].std(ddof=0) or 1.0),
            }
            for indicator, group in data.groupby("indicator")
        },
        "metrics": {
            "mae": round(mae, 6),
            "rmse": round(rmse, 6),
            "r2": None if r2 is None else round(r2, 6),
            "smape_pct": round(smape, 6),
            "train_rows": int(len(train)),
            "test_rows": int(len(test)),
            "holdout_strategy": "latest observation per country-indicator series",
            "per_indicator": per_indicator_metrics,
        },
        "feature_importance": ranked,
        "responsible_use": (
            "Forecasts estimate future aggregate indicator values from historical annual "
            "patterns. They are not outbreak probabilities or clinical predictions."
        ),
    }
    artifact_path = model_directory / FORECAST_ARTIFACT
    joblib.dump(artifact, artifact_path)

    return {
        "kind": artifact["kind"],
        "version": artifact["version"],
        "trained_at": trained_at,
        "artifact": str(artifact_path),
        "dataset_sha256": data_hash,
        "metrics": artifact["metrics"],
        "feature_importance": ranked,
    }
