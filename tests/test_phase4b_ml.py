"""Tests for Project RISING Phase 4B trained ML capabilities."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.ml import router
from api.services.ml_service import MLService
from ml.train_all import train_all_models


def _synthetic_dataset(path: Path) -> None:
    rows: list[dict[str, object]] = []
    countries = ["Philippines", "Indonesia", "Thailand"]
    indicators = ["life_expectancy_rate", "infant_mortality_rate"]
    for country_index, country in enumerate(countries):
        for indicator in indicators:
            for year in range(2000, 2016):
                if indicator == "life_expectancy_rate":
                    value = 65 + country_index * 2 + (year - 2000) * 0.35
                else:
                    value = 38 - country_index * 3 - (year - 2000) * 0.8
                value += np.sin(year + country_index) * 0.15
                rows.append(
                    {
                        "country": country,
                        "year": year,
                        "indicator": indicator,
                        "sub_indicator": None,
                        "sex": None,
                        "unit": None,
                        "value": round(float(value), 4),
                    }
                )
    pd.DataFrame(rows).to_csv(path, index=False)


@pytest.fixture(scope="module")
def trained_environment(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path]:
    root = tmp_path_factory.mktemp("phase4b")
    data_path = root / "health.csv"
    model_directory = root / "models"
    _synthetic_dataset(data_path)
    train_all_models(data_path, model_directory)
    return data_path, model_directory


def test_training_creates_versioned_artifacts(
    trained_environment: tuple[Path, Path],
) -> None:
    _, model_directory = trained_environment
    assert (model_directory / "forecast_model.joblib").exists()
    assert (model_directory / "anomaly_model.joblib").exists()
    assert (model_directory / "registry.json").exists()
    assert (model_directory / "training_report.json").exists()

    registry = MLService(model_directory=model_directory).registry()
    assert registry["phase"] == "4B"
    assert len(registry["models"]) == 2
    assert registry["responsible_use"]["clinically_validated"] is False


def test_ml_forecast_returns_future_predictions(
    trained_environment: tuple[Path, Path],
) -> None:
    data_path, model_directory = trained_environment
    service = MLService(model_directory=model_directory, data_path=data_path)
    result = service.forecast("Philippines", "life_expectancy_rate", 3)

    assert result["is_ml_prediction"] is True
    assert len(result["forecast"]) == 3
    assert result["forecast"][0]["year"] == 2016
    assert result["model"]["type"] == "supervised random forest regression"
    assert result["model"]["holdout_metrics"]["test_rows"] > 0


def test_isolation_forest_flags_extreme_value(
    trained_environment: tuple[Path, Path],
) -> None:
    data_path, model_directory = trained_environment
    service = MLService(model_directory=model_directory, data_path=data_path)
    result = service.anomaly_prediction(
        country="Philippines",
        indicator="infant_mortality_rate",
        year=2016,
        value=5000.0,
        previous_value=26.0,
    )

    assert result["is_ml_prediction"] is True
    assert result["is_anomaly"] is True
    assert result["review_level"] == "high"
    assert result["anomaly_score"] >= 75


def test_drift_report_is_stable_for_training_dataset(
    trained_environment: tuple[Path, Path],
) -> None:
    data_path, model_directory = trained_environment
    service = MLService(model_directory=model_directory, data_path=data_path)
    report = service.drift_report()
    assert report["status"] == "stable"
    assert report["dataset_changed_since_training"] is False


def test_phase4b_api_contract(
    trained_environment: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    data_path, model_directory = trained_environment
    monkeypatch.setenv("RISING_HEALTH_DATA_PATH", str(data_path))
    monkeypatch.setenv("RISING_MODEL_DIR", str(model_directory))

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    readiness = client.get("/api/v1/ml/readiness")
    assert readiness.status_code == 200
    assert readiness.json()["status"] == "ready"

    forecast = client.post(
        "/api/v1/ml/forecast",
        json={
            "country": "Philippines",
            "indicator": "life_expectancy_rate",
            "horizon_years": 2,
        },
    )
    assert forecast.status_code == 200
    assert len(forecast.json()["forecast"]) == 2

    anomaly = client.post(
        "/api/v1/ml/anomaly/predict",
        json={
            "country": "Philippines",
            "indicator": "infant_mortality_rate",
            "year": 2016,
            "value": 5000,
            "previous_value": 26,
        },
    )
    assert anomaly.status_code == 200
    assert anomaly.json()["is_anomaly"] is True
