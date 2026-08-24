"""Feature engineering for forecasting and anomaly detection."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

FORECAST_CATEGORICAL_FEATURES = ["country", "indicator"]
FORECAST_NUMERIC_FEATURES = [
    "year",
    "lag1",
    "lag2",
    "rolling_mean_3",
    "rolling_std_3",
    "trend_delta",
]
ANOMALY_FEATURES = [
    "value_zscore",
    "delta_zscore",
    "year_scaled",
    "has_previous_value",
]


def build_forecast_frame(data: pd.DataFrame) -> pd.DataFrame:
    """Build lagged supervised-learning rows from long-form annual indicators."""
    frame = data.loc[:, ["country", "indicator", "year", "value"]].copy()
    frame = frame.sort_values(["country", "indicator", "year"]).reset_index(drop=True)
    grouped = frame.groupby(["country", "indicator"], sort=False)["value"]

    frame["lag1"] = grouped.shift(1)
    frame["lag2"] = grouped.shift(2)
    frame["rolling_mean_3"] = grouped.transform(
        lambda values: values.shift(1).rolling(window=3, min_periods=2).mean()
    )
    frame["rolling_std_3"] = grouped.transform(
        lambda values: values.shift(1).rolling(window=3, min_periods=2).std(ddof=0)
    )
    frame["trend_delta"] = frame["lag1"] - frame["lag2"]
    frame["rolling_std_3"] = frame["rolling_std_3"].fillna(0.0)
    frame = frame.dropna(subset=["lag1", "lag2", "rolling_mean_3", "value"])
    return frame.reset_index(drop=True)


def time_holdout_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Reserve the latest observation of every sufficiently long series for testing."""
    if frame.empty:
        raise ValueError("Not enough historical observations to train forecasting models.")

    test_indices = (
        frame.groupby(["country", "indicator"], sort=False, group_keys=False)
        .tail(1)
        .index
    )
    test = frame.loc[test_indices].copy()
    train = frame.drop(index=test_indices).copy()

    if train.empty or test.empty:
        raise ValueError("Unable to create a time-based train/test split.")
    return train.reset_index(drop=True), test.reset_index(drop=True)


def build_anomaly_frame(data: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Normalize indicator values and year-over-year changes for Isolation Forest."""
    frame = data.loc[:, ["country", "indicator", "year", "value"]].copy()
    frame = frame.sort_values(["country", "indicator", "year"]).reset_index(drop=True)
    grouped = frame.groupby(["country", "indicator"], sort=False)["value"]
    frame["previous_value"] = grouped.shift(1)
    frame["delta"] = frame["value"] - frame["previous_value"]

    value_stats_df = frame.groupby("indicator")["value"].agg(["mean", "std", "count"])
    delta_stats_df = frame.groupby("indicator")["delta"].agg(["mean", "std", "count"])

    value_stats: dict[str, dict[str, float | int]] = {}
    delta_stats: dict[str, dict[str, float | int]] = {}
    for indicator, row in value_stats_df.iterrows():
        std = float(row["std"]) if pd.notna(row["std"]) and row["std"] > 0 else 1.0
        value_stats[str(indicator)] = {
            "mean": float(row["mean"]),
            "std": std,
            "count": int(row["count"]),
        }
    for indicator, row in delta_stats_df.iterrows():
        mean = float(row["mean"]) if pd.notna(row["mean"]) else 0.0
        std = float(row["std"]) if pd.notna(row["std"]) and row["std"] > 0 else 1.0
        count = int(row["count"]) if pd.notna(row["count"]) else 0
        delta_stats[str(indicator)] = {"mean": mean, "std": std, "count": count}

    frame["value_zscore"] = frame.apply(
        lambda row: (row["value"] - value_stats[row["indicator"]]["mean"])
        / value_stats[row["indicator"]]["std"],
        axis=1,
    )
    frame["has_previous_value"] = frame["previous_value"].notna().astype(float)
    frame["delta_zscore"] = frame.apply(
        lambda row: 0.0
        if pd.isna(row["delta"])
        else (row["delta"] - delta_stats[row["indicator"]]["mean"])
        / delta_stats[row["indicator"]]["std"],
        axis=1,
    )

    year_min = int(frame["year"].min())
    year_max = int(frame["year"].max())
    year_span = max(year_max - year_min, 1)
    frame["year_scaled"] = (frame["year"] - year_min) / year_span

    latest_values: dict[str, dict[str, float | int]] = {}
    for _, row in (
        frame.groupby(["country", "indicator"], sort=False, group_keys=False)
        .tail(1)
        .iterrows()
    ):
        key = f"{row['country']}|||{row['indicator']}"
        latest_values[key] = {"year": int(row["year"]), "value": float(row["value"])}

    indicator_baseline: dict[str, dict[str, float | int]] = {}
    for indicator, group in frame.groupby("indicator"):
        indicator_baseline[str(indicator)] = {
            "mean": float(group["value"].mean()),
            "std": float(group["value"].std(ddof=0) or 1.0),
            "count": int(len(group)),
            "latest_year": int(group["year"].max()),
        }

    baseline: dict[str, Any] = {
        "value_stats": value_stats,
        "delta_stats": delta_stats,
        "year_min": year_min,
        "year_max": year_max,
        "latest_values": latest_values,
        "indicator_baseline": indicator_baseline,
    }
    return frame, baseline


def anomaly_feature_vector(
    *,
    indicator: str,
    year: int,
    value: float,
    previous_value: float | None,
    baseline: dict[str, Any],
) -> tuple[np.ndarray, dict[str, float]]:
    """Create one model-ready anomaly vector and human-readable feature values."""
    value_stats = baseline["value_stats"].get(indicator)
    delta_stats = baseline["delta_stats"].get(indicator)
    if value_stats is None or delta_stats is None:
        raise KeyError(f"Unknown indicator: {indicator}")

    value_zscore = (float(value) - float(value_stats["mean"])) / float(
        value_stats["std"]
    )
    has_previous = 1.0 if previous_value is not None else 0.0
    if previous_value is None:
        delta_zscore = 0.0
    else:
        delta = float(value) - float(previous_value)
        delta_zscore = (delta - float(delta_stats["mean"])) / float(
            delta_stats["std"]
        )

    year_span = max(int(baseline["year_max"]) - int(baseline["year_min"]), 1)
    year_scaled = (int(year) - int(baseline["year_min"])) / year_span
    readable = {
        "value_zscore": float(value_zscore),
        "delta_zscore": float(delta_zscore),
        "year_scaled": float(year_scaled),
        "has_previous_value": float(has_previous),
    }
    vector = np.array([[readable[name] for name in ANOMALY_FEATURES]], dtype=float)
    return vector, readable
