from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from config.config import Settings, get_settings
from main import create_app


def test_production_configuration_rejects_insecure_values() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", cors_origins=("*",))

    with pytest.raises(ValidationError):
        Settings(require_api_key=True, api_key="short")


def test_readiness_reports_missing_required_dataset(tmp_path: Path) -> None:
    application = create_app(
        Settings(environment="test", health_dataset=tmp_path / "missing.csv")
    )
    response = TestClient(application).get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["health_dataset"]["status"] == "fail"


def test_security_headers_and_request_id_are_returned() -> None:
    response = TestClient(create_app(Settings(environment="test"))).get(
        "/health", headers={"X-Request-ID": "test-request-123"}
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "test-request-123"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_render_external_hostname_is_accepted(monkeypatch) -> None:
    hostname = "project-rising-api.onrender.com"
    monkeypatch.setenv("TRUSTED_HOSTS", "localhost,127.0.0.1,testserver")
    monkeypatch.setenv("RENDER_EXTERNAL_HOSTNAME", hostname)

    settings = Settings.from_environment()
    response = TestClient(create_app(settings)).get(
        "/health", headers={"host": hostname}
    )

    assert hostname in settings.trusted_hosts
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_oversized_request_is_rejected() -> None:
    client = TestClient(
        create_app(Settings(environment="test", max_request_body_bytes=1024))
    )
    response = client.post(
        "/api/v1/disease-risk/predict",
        content=b"x" * 1025,
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json()["error"] == "payload_too_large"


def test_api_key_protects_prediction_and_metrics(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("REQUIRE_API_KEY", "true")
    monkeypatch.setenv("API_KEY", "pilot-secret-key-123456")
    get_settings.cache_clear()
    try:
        client = TestClient(create_app(get_settings()))
        assert client.get("/metrics").status_code == 401
        assert client.post("/api/v1/disease-risk/predict", json={}).status_code == 401
        response = client.get(
            "/metrics", headers={"X-API-Key": "pilot-secret-key-123456"}
        )
        assert response.status_code == 200
        assert "rising_http_requests_total" in response.text
    finally:
        get_settings.cache_clear()


def test_validation_error_has_stable_error_envelope() -> None:
    response = TestClient(create_app(Settings(environment="test"))).post(
        "/api/v1/disease-risk/predict",
        json={
            "country": "Philippines",
            "disease": "dengue",
            "temperature_c": 29,
            "rainfall_mm": -1,
            "humidity_pct": 85,
            "unexpected": "rejected",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"
    assert response.json()["request_id"]
