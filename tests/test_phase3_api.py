from fastapi.testclient import TestClient

from api.config import API_VERSION
from main import app


client = TestClient(app)


def test_root_version() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["version"] == API_VERSION


def test_health_indicator_filter() -> None:
    response = client.get(
        "/api/v1/health-indicators",
        params={"country": "Brunei", "indicator": "crude_birth_ratio", "limit": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 3
    assert all(row["country"] == "Brunei" for row in body["data"])


def test_country_profile() -> None:
    response = client.get("/api/v1/countries/Philippines/profile")
    assert response.status_code == 200
    assert response.json()["indicator_count"] > 0


def test_country_risk() -> None:
    response = client.get("/api/v1/countries/Philippines/risk")
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["risk_score"] <= 100
    assert body["is_ai_prediction"] is False


def test_disease_risk() -> None:
    response = client.post(
        "/api/v1/disease-risk/predict",
        json={
            "country": "Philippines",
            "disease": "dengue",
            "temperature_c": 29.0,
            "rainfall_mm": 180.0,
            "humidity_pct": 85.0,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["forecast_window"] == "next 14 days"
    assert len(body["recommendations"]) == 2


def test_operational_endpoints() -> None:
    quality = client.get("/api/v1/data-quality")
    pipeline = client.get("/api/v1/pipeline/status")
    readiness = client.get("/api/v1/readiness")
    assert quality.status_code == 200
    assert quality.json()["record_count"] > 0
    assert pipeline.json()["batch_pipeline"]["status"] == "ready"
    assert readiness.json()["status"] in {"ready", "not_ready"}


def test_anomaly_endpoint() -> None:
    response = client.get("/api/v1/anomalies", params={"limit": 5})
    assert response.status_code == 200
    assert response.json()["count"] <= 5
