"""Phase 4 real-time alerting, root-cause analysis, and forecasting API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.phase4_schemas import AcknowledgeRequest, EvaluateRequest, OperationalEvent
from api.services.alert_service import (
    acknowledge_alert,
    create_alert,
    evaluate_current_state,
    get_alerts,
    summarize_alerts,
)
from api.services.forecast_service import forecast_health_indicator
from api.services.incident_store import list_alerts


router = APIRouter(prefix="/operations", tags=["Phase 4 Operations Intelligence"])


@router.post("/events", status_code=201)
def ingest_operational_event(event: OperationalEvent) -> dict[str, Any]:
    """Normalize an incoming signal and create or update an alert."""

    alert = create_alert(event)
    return {"status": "accepted", "alert": alert}


@router.get("/alerts")
def list_operational_alerts(
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    country: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict[str, Any]:
    """Return filtered operational alerts."""

    alerts = get_alerts(status=status, severity=severity, country=country, limit=limit)
    return {"count": len(alerts), "data": alerts}


@router.get("/alerts/summary")
def alert_summary() -> dict[str, Any]:
    """Return the operations-center alert summary."""

    return summarize_alerts()


@router.post("/alerts/evaluate")
def evaluate_alerts(request: EvaluateRequest) -> dict[str, Any]:
    """Evaluate current pipeline, freshness, quality, and anomaly signals."""

    return evaluate_current_state(
        stale_after_hours=request.stale_after_hours,
        anomaly_limit=request.anomaly_limit,
        include_anomalies=request.include_anomalies,
    )


@router.patch("/alerts/{alert_id}/acknowledge")
def acknowledge_operational_alert(
    alert_id: str,
    request: AcknowledgeRequest,
) -> dict[str, Any]:
    """Record human ownership of an alert."""

    alert = acknowledge_alert(alert_id, request.owner, request.note)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")
    return alert


@router.get("/incidents/{alert_id}/root-cause")
def incident_root_cause(alert_id: str) -> dict[str, Any]:
    """Return the stored explainable root-cause analysis for an alert."""

    alert = next((item for item in list_alerts() if item.get("id") == alert_id), None)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")
    return {
        "alert_id": alert_id,
        "title": alert.get("title"),
        "severity": alert.get("severity"),
        "status": alert.get("status"),
        "root_cause": alert.get("root_cause"),
        "recovery_plan": alert.get("recovery_plan"),
    }


@router.get("/forecast")
def health_indicator_forecast(
    country: str = Query(min_length=2),
    indicator: str = Query(min_length=2),
    horizon_years: int = Query(default=3, ge=1, le=5),
) -> dict[str, Any]:
    """Forecast an annual health indicator using transparent historical trend logic."""

    try:
        return forecast_health_indicator(
            country,
            indicator,
            horizon_years=horizon_years,
        )
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/readiness")
def phase4_readiness() -> dict[str, Any]:
    """Report which Phase 4 capabilities are available."""

    summary = summarize_alerts()
    return {
        "status": "ready",
        "phase": 4,
        "capabilities": {
            "real_time_event_ingestion": True,
            "persistent_alert_lifecycle": True,
            "root_cause_analysis": True,
            "guided_recovery": True,
            "historical_health_forecasting": True,
            "automatic_destructive_recovery": False,
        },
        "alert_summary": summary,
        "responsible_use": (
            "Signals support operational and public-health preparedness. "
            "Human verification remains required."
        ),
    }
