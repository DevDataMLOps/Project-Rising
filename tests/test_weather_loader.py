import json
from datetime import timezone

from warehouse.weather_loader import (
    date_key_from_timestamp,
    iter_jsonl_events,
    load_weather_events_jsonl,
    parse_event_timestamp,
)


class FakeConnection:
    pass


class FakeTransaction:
    def __enter__(self):
        return FakeConnection()

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class FakeEngine:
    def begin(self):
        return FakeTransaction()


def test_parse_event_timestamp_handles_zulu_time():
    observed_at = parse_event_timestamp("2026-07-12T09:15:30Z")

    assert observed_at.year == 2026
    assert observed_at.month == 7
    assert observed_at.day == 12
    assert observed_at.tzinfo == timezone.utc


def test_date_key_from_timestamp_returns_yyyymmdd_integer():
    assert date_key_from_timestamp("2026-07-12T09:15:30Z") == 20260712


def test_iter_jsonl_events_reads_non_empty_lines(tmp_path):
    input_path = tmp_path / "accepted_weather_events.jsonl"
    events = [
        {"event_id": "event-001", "country": "Indonesia"},
        {"event_id": "event-002", "country": "Thailand"},
    ]

    input_path.write_text(
        "\n".join(json.dumps(event) for event in events) + "\n\n",
        encoding="utf-8",
    )

    assert iter_jsonl_events(input_path) == events


def test_iter_jsonl_events_returns_empty_list_for_missing_file(tmp_path):
    assert iter_jsonl_events(tmp_path / "missing.jsonl") == []


def test_load_weather_events_jsonl_counts_inserts_and_duplicates(
    tmp_path,
    monkeypatch,
):
    input_path = tmp_path / "accepted_weather_events.jsonl"
    events = [
        {"event_id": "event-001"},
        {"event_id": "event-002"},
        {"event_id": "event-003"},
    ]
    insert_results = iter([True, False, True])

    input_path.write_text(
        "\n".join(json.dumps(event) for event in events),
        encoding="utf-8",
    )

    def fake_load_weather_event(connection, event):
        assert isinstance(connection, FakeConnection)
        assert event in events
        return next(insert_results)

    monkeypatch.setattr(
        "warehouse.weather_loader.load_weather_event",
        fake_load_weather_event,
    )

    counts = load_weather_events_jsonl(
        input_path=input_path,
        engine=FakeEngine(),
    )

    assert counts == {
        "input": 3,
        "inserted": 2,
        "duplicates": 1,
    }
