"""Create judge-ready Phase 4 alerts against a running local API."""

from __future__ import annotations

import json
from urllib import request


BASE_URL = "http://127.0.0.1:8000/api/v1/operations"

EVENTS = [
    {
        "event_type": "pipeline_failure",
        "source": "streaming_consumer",
        "status": "failed",
        "message": "Climate events failed schema validation and entered the DLQ.",
        "metric": "dlq_count",
        "value": 14,
        "threshold": 3,
        "metadata": {"dlq_count": 14, "retry_count": 3},
    },
    {
        "event_type": "climate_risk",
        "source": "weather_feed",
        "status": "warning",
        "country": "Philippines",
        "message": "Heavy rainfall and humidity increased mosquito-borne disease preparedness risk.",
        "metadata": {
            "temperature_c": 29,
            "rainfall_mm": 220,
            "humidity_pct": 88,
        },
    },
]


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    for event in EVENTS:
        result = post_json(f"{BASE_URL}/events", event)
        alert = result["alert"]
        print(f"Created {alert['severity']} alert: {alert['title']}")
    evaluation = post_json(
        f"{BASE_URL}/alerts/evaluate",
        {"stale_after_hours": 720, "anomaly_limit": 5, "include_anomalies": True},
    )
    print(json.dumps(evaluation["summary"], indent=2))


if __name__ == "__main__":
    main()
