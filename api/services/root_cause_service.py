"""Explainable root-cause analysis for Project RISING operational signals."""

from __future__ import annotations

from typing import Any


RULES: dict[str, dict[str, Any]] = {
    "pipeline_failure": {
        "title": "Pipeline delivery failure",
        "causes": [
            ("Source data is missing, late, or inaccessible", 0.82),
            ("Schema drift caused validation or transformation failure", 0.74),
            ("A downstream warehouse or storage dependency is unavailable", 0.61),
        ],
        "actions": [
            "Retry from the last successful checkpoint.",
            "Route malformed records to the dead-letter queue instead of blocking the batch.",
            "Validate source availability, schema version, and warehouse connectivity.",
        ],
        "prevention": [
            "Add freshness and schema-contract checks before transformation.",
            "Track retry count, DLQ volume, and checkpoint age as alertable metrics.",
        ],
    },
    "data_quality": {
        "title": "Data-quality degradation",
        "causes": [
            ("Required values are missing or malformed", 0.86),
            ("Duplicate or replayed records bypassed idempotency controls", 0.72),
            ("A source-system definition changed without a matching contract update", 0.65),
        ],
        "actions": [
            "Quarantine failing records and preserve accepted records.",
            "Compare the current schema and key fields with the last trusted run.",
            "Re-run validation after correcting the source or transformation rule.",
        ],
        "prevention": [
            "Version schemas and enforce required-field, range, and uniqueness checks.",
            "Publish quality metrics with every pipeline run.",
        ],
    },
    "api_health": {
        "title": "API availability or latency incident",
        "causes": [
            ("The application process restarted or failed its health check", 0.78),
            ("A required file, model, or database dependency is unavailable", 0.71),
            ("Traffic or a slow dependency increased request latency", 0.58),
        ],
        "actions": [
            "Check application logs and the /health endpoint.",
            "Verify processed data and external dependency availability.",
            "Restart the service only after preserving incident evidence.",
        ],
        "prevention": [
            "Add readiness checks for data, model, and warehouse dependencies.",
            "Track error rate and p95 latency separately from process uptime.",
        ],
    },
    "climate_risk": {
        "title": "Climate-driven operational pressure",
        "causes": [
            ("Heavy rainfall or flooding increased disruption and vector habitat", 0.83),
            ("Heat or humidity moved conditions into a disease-favorable range", 0.76),
            ("Infrastructure disruption delayed health-data delivery", 0.62),
        ],
        "actions": [
            "Escalate climate-health surveillance for the affected country.",
            "Pre-position local data buffering and offline continuity procedures.",
            "Validate facilities, transport routes, and communication dependencies.",
        ],
        "prevention": [
            "Integrate live weather feeds and regional disruption thresholds.",
            "Maintain local cache, delayed synchronization, and failover playbooks.",
        ],
    },
    "disease_risk": {
        "title": "Elevated disease-risk signal",
        "causes": [
            ("Weather conditions are favorable for transmission or vector survival", 0.84),
            ("Historical health indicators show elevated population vulnerability", 0.73),
            ("Recent health observations differ from the expected baseline", 0.66),
        ],
        "actions": [
            "Verify the signal with local surveillance and public-health teams.",
            "Increase case surveillance and targeted public-health messaging.",
            "Pre-position diagnostics, treatment supplies, and response staff.",
        ],
        "prevention": [
            "Continuously recalibrate thresholds with verified outbreak labels.",
            "Keep the model explainable and require human confirmation before action.",
        ],
    },
    "recovery": {
        "title": "Recovery confirmation",
        "causes": [
            ("The affected dependency or data flow returned to a healthy state", 0.90),
            ("Retry, checkpoint replay, or manual correction restored service", 0.76),
        ],
        "actions": [
            "Verify data completeness from the last known-good checkpoint.",
            "Resolve related alerts only after health and quality checks pass.",
        ],
        "prevention": [
            "Record the recovery method and time-to-recovery for future automation.",
        ],
    },
}


def _metadata_evidence(metadata: dict[str, Any]) -> list[str]:
    evidence: list[str] = []
    interesting = {
        "missing_file": "Missing source or output file",
        "schema_errors": "Schema validation errors",
        "validation_failures": "Record validation failures",
        "duplicate_rate": "Duplicate-record rate",
        "dlq_count": "Dead-letter queue count",
        "retry_count": "Retry count",
        "latency_ms": "Observed latency in milliseconds",
        "last_success_minutes": "Minutes since last successful run",
        "rainfall_mm": "Rainfall in millimetres",
        "humidity_pct": "Relative humidity percentage",
        "temperature_c": "Temperature in Celsius",
        "risk_score": "Health-risk score",
    }
    for key, label in interesting.items():
        if key in metadata:
            evidence.append(f"{label}: {metadata[key]}")
    return evidence


def analyze_root_cause(
    event_type: str,
    *,
    message: str,
    source: str,
    country: str | None = None,
    metric: str | None = None,
    value: float | None = None,
    threshold: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return ranked causes, evidence, and a recovery plan."""

    rule = RULES.get(event_type, RULES["api_health"])
    metadata = metadata or {}
    evidence = [f"Source: {source}", f"Signal: {message}"]
    if country:
        evidence.append(f"Country: {country}")
    if metric:
        evidence.append(f"Metric: {metric}")
    if value is not None:
        evidence.append(f"Observed value: {value}")
    if threshold is not None:
        evidence.append(f"Threshold: {threshold}")
    evidence.extend(_metadata_evidence(metadata))

    causes = [
        {
            "rank": index,
            "cause": cause,
            "confidence": confidence,
        }
        for index, (cause, confidence) in enumerate(rule["causes"], start=1)
    ]
    return {
        "analysis_type": "explainable rule-based root-cause analysis",
        "summary": rule["title"],
        "probable_causes": causes,
        "evidence": evidence,
        "corrective_actions": list(rule["actions"]),
        "prevention_actions": list(rule["prevention"]),
        "human_verification_required": True,
    }
