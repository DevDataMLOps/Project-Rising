from streaming.consumer import (
    event_fingerprint,
    process_weather_event,
)


def valid_weather_event() -> dict:
    return {
        "event_id": "event-1",
        "station_id": "TH-BKK-01",
        "country": "Thailand",
        "timestamp": "2026-06-21T14:05:00Z",
        "temperature_c": 34.2,
        "humidity_pct": 81.0,
        "rainfall_mm": 12.4,
    }


def test_event_fingerprint_is_stable():
    event = valid_weather_event()

    assert event_fingerprint(event) == event_fingerprint(event.copy())


def test_duplicate_event_is_not_loaded_twice(tmp_path):
    event = valid_weather_event()
    accepted_path = tmp_path / "accepted.jsonl"
    checkpoint_path = tmp_path / "checkpoints.txt"
    dlq_path = tmp_path / "dlq.jsonl"

    first_status = process_weather_event(
        event=event,
        accepted_path=accepted_path,
        checkpoint_path=checkpoint_path,
        dlq_path=dlq_path,
    )
    second_status = process_weather_event(
        event=event,
        accepted_path=accepted_path,
        checkpoint_path=checkpoint_path,
        dlq_path=dlq_path,
    )

    assert first_status == "accepted"
    assert second_status == "duplicate"
    assert len(accepted_path.read_text().splitlines()) == 1
