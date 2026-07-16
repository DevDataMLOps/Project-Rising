from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["project"] == "Project RISING"
    assert response.json()["version"] == "2.0.0"


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_filtered_health_indicators() -> None:
    response = client.get(
        "/api/v1/health-indicators",
        params={
            "country": "Brunei",
            "indicator": "crude_birth_ratio",
            "limit": 3,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 3
    assert len(body["data"]) == 3

    for record in body["data"]:
        assert record["country"] == "Brunei"
        assert record["indicator"] == "crude_birth_ratio"


def test_country_list() -> None:
    response = client.get(
        "/api/v1/health-indicators/countries"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 10
    assert "Brunei" in body["countries"]
    assert "Philippines" in body["countries"]


def test_indicator_list() -> None:
    response = client.get(
        "/api/v1/health-indicators/indicators"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["count"] > 0
    assert "crude_birth_ratio" in body["indicators"]


def test_pipeline_status() -> None:
    response = client.get("/api/v1/pipeline/status")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "healthy"
    assert body["batch_pipeline"]["status"] == "ready"
    assert body["batch_pipeline"]["record_count"] > 0
    assert (
        body["streaming_pipeline"]["status"]
        == "not_configured"
    )


def test_climate_events_status() -> None:
    response = client.get("/api/v1/climate-events")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "not_configured"
    assert body["count"] == 0
    assert body["data"] == []


def test_country_risk() -> None:
    response = client.get(
        "/api/v1/countries/Philippines/risk"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["country"] == "Philippines"
    assert 0 <= body["risk_score"] <= 100
    assert body["risk_level"] in {
        "low",
        "moderate",
        "high",
    }
    assert body["indicators_used"] > 0
    assert body["is_ai_prediction"] is False


def test_disease_risk_prediction() -> None:
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
    assert body["country"] == "Philippines"
    assert body["disease"] == "Dengue"
    assert body["forecast_window"] == "next 14 days"
    assert 0 <= body["risk_probability"] <= 1
    assert body["risk_level"] in {"low", "moderate", "high"}
    assert body["model"]["version"] == "1.0.0"
    assert len(body["health_evidence"]) > 0
    assert len(body["recommendations"]) == 2


def test_disease_risk_sample_is_real_output() -> None:
    response = client.get("/api/v1/disease-risk/sample")

    assert response.status_code == 200
    assert response.json()["risk_score"] > 0


def test_disease_risk_rejects_invalid_weather_input() -> None:
    response = client.post(
        "/api/v1/disease-risk/predict",
        json={
            "country": "Philippines",
            "disease": "dengue",
            "temperature_c": 29.0,
            "rainfall_mm": -1,
            "humidity_pct": 85.0,
        },
    )

    assert response.status_code == 422
