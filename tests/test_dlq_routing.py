import json

from streaming.consumer import process_weather_event
from streaming.dlq_handler import build_dlq_record, write_dlq_record


def test_build_dlq_record_preserves_error_context():
    payload = {"event_id": "bad-event"}
    error = ValueError("country is missing")

    dlq_record = build_dlq_record(
        original_payload=payload,
        error=error,
        retry_count=5,
        source_topic="weather-events",
    )

    assert dlq_record["original_payload"] == payload
    assert dlq_record["error_type"] == "ValueError"
    assert dlq_record["error_message"] == "country is missing"
    assert dlq_record["retry_count"] == 5
    assert dlq_record["source_topic"] == "weather-events"
    assert "failed_at" in dlq_record


def test_write_dlq_record_appends_jsonl(tmp_path):
    output_path = tmp_path / "weather_events_dlq.jsonl"
    dlq_record = {
        "original_payload": {"event_id": "bad-event"},
        "error_type": "ValueError",
        "error_message": "country is missing",
        "retry_count": 5,
        "failed_at": "2026-06-21T14:10:00Z",
        "source_topic": "weather-events",
    }

    write_dlq_record(dlq_record, output_path)

    written_record = json.loads(output_path.read_text())
    assert written_record == dlq_record


def test_invalid_event_routes_to_dlq_after_retries(tmp_path):
    event = {
        "event_id": "bad-event",
        "station_id": "TH-BKK-01",
        "timestamp": "2026-06-21T14:05:00Z",
        "temperature_c": 34.2,
        "humidity_pct": 81.0,
        "rainfall_mm": 12.4,
        "retry_count": 5,
    }

    status = process_weather_event(
        event=event,
        accepted_path=tmp_path / "accepted.jsonl",
        checkpoint_path=tmp_path / "checkpoints.txt",
        dlq_path=tmp_path / "dlq.jsonl",
    )

    assert status == "dlq"
    assert "bad-event" in (tmp_path / "dlq.jsonl").read_text()
