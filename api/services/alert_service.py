"""Real-time alert creation, evaluation, and lifecycle management."""

from __future__ import annotations

import csv
import hashlib
import importlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from api.phase4_schemas import OperationalEvent
from api.services.incident_store import list_alerts, update_alert, upsert_alert
from api.services.root_cause_service import analyze_root_cause


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HEALTH_DATASET = PROJECT_ROOT / "data" / "processed" / "asean_health_indicators.csv"

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def determine_severity(event: OperationalEvent) -> str:
    """Map normalized event details into an operational severity."""

    if event.status == "critical":
        return "critical"
    if event.value is not None and event.threshold is not None:
        if event.threshold == 0 and event.value > 0:
            return "high"
        if event.threshold != 0:
            ratio = event.value / event.threshold
            if ratio >= 1.5:
                return "critical"
            if ratio >= 1:
                return "high"
    if event.status in {"failed", "error"}:
        return "high"
    if event.status in {"warning", "degraded"}:
        return "medium"
    if event.event_type in {"climate_risk", "disease_risk"}:
        return "medium"
    if event.status in {"recovered", "healthy", "info"}:
        return "info"
    return "low"


def _dedup_key(event: OperationalEvent) -> str:
    raw = "|".join(
        [
            event.event_type,
            event.source.casefold(),
            (event.country or "global").casefold(),
            (event.metric or "general").casefold(),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def create_alert(event: OperationalEvent) -> dict[str, Any]:
    """Convert an event into a persistent, explainable alert."""

    now = _utc_now()
    severity = determine_severity(event)
    root_cause = analyze_root_cause(
        event.event_type,
        message=event.message,
        source=event.source,
        country=event.country,
        metric=event.metric,
        value=event.value,
        threshold=event.threshold,
        metadata=event.metadata,
    )
    status = "resolved" if event.status in {"recovered", "healthy"} else "open"
    title = root_cause["summary"]
    if event.country:
        title = f"{title}: {event.country}"

    alert = {
        "id": str(uuid4()),
        "dedup_key": _dedup_key(event),
        "title": title,
        "category": event.event_type,
        "severity": severity,
        "status": status,
        "source": event.source,
        "country": event.country,
        "metric": event.metric,
        "message": event.message,
        "observed_value": event.value,
        "threshold": event.threshold,
        "created_at": now,
        "updated_at": now,
        "last_seen_at": event.observed_at.isoformat() if event.observed_at else now,
        "occurrences": 1,
        "metadata": event.metadata,
        "root_cause": root_cause,
        "recommended_actions": root_cause["corrective_actions"],
        "recovery_plan": {
            "mode": "human-approved guided recovery",
            "steps": root_cause["corrective_actions"],
            "automatic_execution_enabled": False,
        },
        "acknowledgement": None,
    }
    return upsert_alert(alert)


def get_alerts(
    *,
    status: str | None = None,
    severity: str | None = None,
    country: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Filter and sort alerts newest-first."""

    alerts = list_alerts()
    if status:
        alerts = [item for item in alerts if item.get("status") == status]
    if severity:
        alerts = [item for item in alerts if item.get("severity") == severity]
    if country:
        alerts = [
            item
            for item in alerts
            if (item.get("country") or "").casefold() == country.casefold()
        ]
    alerts.sort(
        key=lambda item: (
            SEVERITY_ORDER.get(str(item.get("severity")), -1),
            str(item.get("updated_at", "")),
        ),
        reverse=True,
    )
    return alerts[:limit]


def summarize_alerts() -> dict[str, Any]:
    """Return an operations-center summary."""

    alerts = list_alerts()
    by_severity = {key: 0 for key in SEVERITY_ORDER}
    by_status: dict[str, int] = {}
    for alert in alerts:
        severity = str(alert.get("severity", "low"))
        status = str(alert.get("status", "open"))
        by_severity[severity] = by_severity.get(severity, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
    open_alerts = [item for item in alerts if item.get("status") == "open"]
    highest = max(
        (str(item.get("severity", "info")) for item in open_alerts),
        key=lambda item: SEVERITY_ORDER.get(item, -1),
        default="none",
    )
    return {
        "total_alerts": len(alerts),
        "open_alerts": len(open_alerts),
        "highest_open_severity": highest,
        "by_severity": by_severity,
        "by_status": by_status,
        "operational_state": "attention_required" if open_alerts else "stable",
    }


def acknowledge_alert(alert_id: str, owner: str, note: str | None) -> dict[str, Any] | None:
    """Acknowledge an alert without hiding or deleting it."""

    now = _utc_now()
    return update_alert(
        alert_id,
        {
            "status": "acknowledged",
            "updated_at": now,
            "acknowledgement": {
                "owner": owner,
                "note": note,
                "acknowledged_at": now,
            },
        },
    )


def _fallback_pipeline_status() -> dict[str, Any]:
    exists = HEALTH_DATASET.exists()
    record_count = 0
    last_modified = None
    if exists:
        with HEALTH_DATASET.open("r", encoding="utf-8-sig", newline="") as csv_file:
            record_count = sum(1 for _ in csv.DictReader(csv_file))
        last_modified = datetime.fromtimestamp(
            HEALTH_DATASET.stat().st_mtime,
            tz=timezone.utc,
        ).isoformat()
    return {
        "status": "healthy" if exists else "degraded",
        "batch_pipeline": {
            "status": "ready" if exists else "missing",
            "record_count": record_count,
            "last_modified_utc": last_modified,
        },
        "streaming_pipeline": {"status": "not_configured", "failed_events": 0},
    }


def current_pipeline_status() -> dict[str, Any]:
    """Use the existing Phase 2 service when available."""

    try:
        module = importlib.import_module("api.services.data_service")
        return module.get_pipeline_status()
    except (ImportError, AttributeError, FileNotFoundError):
        return _fallback_pipeline_status()


def _quality_snapshot() -> dict[str, Any] | None:
    try:
        module = importlib.import_module("api.services.quality_service")
        function = getattr(module, "data_quality_report")
        return function()
    except (ImportError, AttributeError, FileNotFoundError, ValueError):
        return None


def _anomaly_snapshot(limit: int) -> dict[str, Any] | None:
    try:
        module = importlib.import_module("api.services.anomaly_service")
        function = getattr(module, "detect_anomalies")
        return function(limit=limit)
    except (ImportError, AttributeError, FileNotFoundError, ValueError):
        return None


def evaluate_current_state(
    *,
    stale_after_hours: int = 720,
    anomaly_limit: int = 10,
    include_anomalies: bool = True,
) -> dict[str, Any]:
    """Evaluate pipeline, quality, freshness, and historical anomaly signals."""

    generated: list[dict[str, Any]] = []
    pipeline = current_pipeline_status()
    batch = pipeline.get("batch_pipeline", {})
    streaming = pipeline.get("streaming_pipeline", {})

    if pipeline.get("status") not in {"healthy", "ready"} or batch.get("status") not in {
        "ready",
        "healthy",
    }:
        generated.append(
            create_alert(
                OperationalEvent(
                    event_type="pipeline_failure",
                    source="batch_pipeline",
                    status="failed",
                    message="Processed ASEAN health data is unavailable or the batch pipeline is not ready.",
                    metadata={"pipeline_status": pipeline},
                )
            )
        )

    failed_events = int(streaming.get("failed_events") or 0)
    if failed_events > 0:
        generated.append(
            create_alert(
                OperationalEvent(
                    event_type="pipeline_failure",
                    source="streaming_pipeline",
                    status="warning",
                    message="Streaming events failed and require retry or DLQ review.",
                    metric="failed_events",
                    value=float(failed_events),
                    threshold=1.0,
                    metadata={"failed_events": failed_events},
                )
            )
        )

    last_modified_raw = batch.get("last_modified_utc")
    if last_modified_raw:
        try:
            last_modified = datetime.fromisoformat(str(last_modified_raw).replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - last_modified).total_seconds() / 3600
            if age_hours > stale_after_hours:
                generated.append(
                    create_alert(
                        OperationalEvent(
                            event_type="data_quality",
                            source="batch_pipeline",
                            status="warning",
                            message="The processed health dataset is older than the configured freshness threshold.",
                            metric="dataset_age_hours",
                            value=round(age_hours, 2),
                            threshold=float(stale_after_hours),
                            metadata={"last_modified_utc": last_modified_raw},
                        )
                    )
                )
        except (TypeError, ValueError):
            pass

    quality = _quality_snapshot()
    if quality and quality.get("status") not in {"pass", "healthy"}:
        failures = int(quality.get("required_field_failures") or 0)
        duplicates = int(quality.get("duplicate_records") or 0)
        generated.append(
            create_alert(
                OperationalEvent(
                    event_type="data_quality",
                    source="phase3_quality_service",
                    status="warning",
                    message="The processed health dataset failed one or more quality checks.",
                    metric="quality_failures",
                    value=float(failures + duplicates),
                    threshold=0.0,
                    metadata={
                        "validation_failures": failures,
                        "duplicate_records": duplicates,
                    },
                )
            )
        )

    anomalies = _anomaly_snapshot(anomaly_limit) if include_anomalies else None
    if anomalies:
        for anomaly in anomalies.get("data", [])[:anomaly_limit]:
            if anomaly.get("severity") not in {"high", "critical"}:
                continue
            generated.append(
                create_alert(
                    OperationalEvent(
                        event_type="disease_risk",
                        source="phase3_anomaly_service",
                        status="warning",
                        country=anomaly.get("country"),
                        metric=anomaly.get("indicator"),
                        value=anomaly.get("z_score"),
                        threshold=2.5,
                        message=str(anomaly.get("reason", "Historical anomaly detected")),
                        metadata=anomaly,
                    )
                )
            )

    return {
        "checked_at": _utc_now(),
        "generated_alert_count": len(generated),
        "generated_alerts": generated,
        "pipeline_snapshot": pipeline,
        "quality_snapshot": quality,
        "anomaly_snapshot": anomalies,
        "summary": summarize_alerts(),
    }
