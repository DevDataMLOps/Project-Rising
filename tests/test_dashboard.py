import json

from demo import pipeline_operations_dashboard as dashboard


def test_read_jsonl_skips_malformed_records(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    valid_record = {"event_id": "valid-event"}
    path.write_text(
        f"{json.dumps(valid_record)}\nnot-json\n\n",
        encoding="utf-8",
    )

    assert dashboard.read_jsonl(path) == [valid_record]


def test_demo_outputs_exist_rejects_invalid_jsonl(tmp_path, monkeypatch) -> None:
    input_path = tmp_path / "weather_events.jsonl"
    accepted_path = tmp_path / "accepted_weather_events.jsonl"
    dlq_path = tmp_path / "weather_events_dlq.jsonl"
    checkpoint_path = tmp_path / "checkpoints.txt"

    input_path.write_text("not-json\n", encoding="utf-8")
    accepted_path.write_text('{"event_id": "accepted"}\n', encoding="utf-8")
    dlq_path.write_text('{"event_id": "failed"}\n', encoding="utf-8")
    checkpoint_path.write_text("fingerprint\n", encoding="utf-8")

    monkeypatch.setattr(dashboard, "INPUT_PATH", input_path)
    monkeypatch.setattr(dashboard, "ACCEPTED_PATH", accepted_path)
    monkeypatch.setattr(dashboard, "DLQ_PATH", dlq_path)
    monkeypatch.setattr(dashboard, "CHECKPOINT_PATH", checkpoint_path)

    assert dashboard.demo_outputs_exist() is False
