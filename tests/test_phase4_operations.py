from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.operations import router
from api.services.incident_store import clear_alerts


app = FastAPI()
app.include_router(router, prefix="/api/v1")
client = TestClient(app)


def setup_function() -> None:
    store = Path(__file__).parent / ".phase4_test_alerts.json"
    os.environ["RISING_ALERT_STORE"] = str(store)
    clear_alerts()


def teardown_function() -> None:
    path = Path(os.environ["RISING_ALERT_STORE"])
    if path.exists():
        path.unlink()
    os.environ.pop("RISING_ALERT_STORE", None)


def test_ingest_alert_and_root_cause() -> None:
    response = client.post(
        "/api/v1/operations/events",
        json={
            "event_type": "pipeline_failure",
            "source": "streaming_consumer",
            "status": "failed",
            "message": "Weather event processing stopped after repeated validation failures.",
            "metric": "validation_failures",
            "value": 12,
            "threshold": 1,
            "metadata": {"validation_failures": 12, "dlq_count": 12},
        },
    )
    assert response.status_code == 201
    alert = response.json()["alert"]
    assert alert["severity"] == "critical"
    assert alert["root_cause"]["probable_causes"]

    root_cause = client.get(
        f"/api/v1/operations/incidents/{alert['id']}/root-cause"
    )
    assert root_cause.status_code == 200
    assert root_cause.json()["recovery_plan"]["automatic_execution_enabled"] is False


def test_alert_deduplication_and_acknowledgement() -> None:
    payload = {
        "event_type": "api_health",
        "source": "fastapi",
        "status": "degraded",
        "message": "p95 latency exceeded the operational threshold.",
        "metric": "latency_ms",
        "value": 850,
        "threshold": 500,
    }
    first = client.post("/api/v1/operations/events", json=payload).json()["alert"]
    second = client.post("/api/v1/operations/events", json=payload).json()["alert"]
    assert first["id"] == second["id"]
    assert second["occurrences"] == 2

    acknowledged = client.patch(
        f"/api/v1/operations/alerts/{first['id']}/acknowledge",
        json={"owner": "platform-team", "note": "Investigating dependency latency."},
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"


def test_alert_summary() -> None:
    client.post(
        "/api/v1/operations/events",
        json={
            "event_type": "climate_risk",
            "source": "weather_feed",
            "status": "warning",
            "country": "Philippines",
            "message": "Heavy rainfall and high humidity increased dengue preparedness risk.",
            "metadata": {"rainfall_mm": 220, "humidity_pct": 88},
        },
    )
    response = client.get("/api/v1/operations/alerts/summary")
    assert response.status_code == 200
    assert response.json()["open_alerts"] == 1
    assert response.json()["operational_state"] == "attention_required"


def test_health_forecast() -> None:
    response = client.get(
        "/api/v1/operations/forecast",
        params={
            "country": "Philippines",
            "indicator": "infant_mortality_rate",
            "horizon_years": 3,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["country"] == "Philippines"
    assert len(payload["historical"]) >= 2
    assert len(payload["forecast"]) == 3
    assert payload["model"]["is_clinically_validated"] is False


def test_readiness() -> None:
    response = client.get("/api/v1/operations/readiness")
    assert response.status_code == 200
    assert response.json()["phase"] == 4
    assert response.json()["capabilities"]["root_cause_analysis"] is True
