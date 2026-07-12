from __future__ import annotations

import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from streaming.consumer import (  # noqa: E402
    process_weather_event,
    process_weather_events_file,
)
from streaming.producer import (  # noqa: E402
    generate_weather_event,
    write_weather_events,
)


STREAMING_DIR = PROJECT_ROOT / "data" / "streaming"
INPUT_PATH = STREAMING_DIR / "weather_events.jsonl"
ACCEPTED_PATH = STREAMING_DIR / "accepted_weather_events.jsonl"
DLQ_PATH = STREAMING_DIR / "weather_events_dlq.jsonl"
CHECKPOINT_PATH = STREAMING_DIR / "checkpoints.txt"


def reset_demo_outputs() -> None:
    """
    Remove previous demo outputs so each run is easy to inspect.
    """
    STREAMING_DIR.mkdir(parents=True, exist_ok=True)

    for path in [
        INPUT_PATH,
        ACCEPTED_PATH,
        DLQ_PATH,
        CHECKPOINT_PATH,
    ]:
        if path.exists():
            path.unlink()


def read_jsonl(path: Path) -> list[dict]:
    """
    Read a JSONL file into dictionaries.
    """
    if not path.exists():
        return []

    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def print_counts() -> None:
    accepted_count = len(read_jsonl(ACCEPTED_PATH))
    dlq_count = len(read_jsonl(DLQ_PATH))
    checkpoint_count = (
        len(CHECKPOINT_PATH.read_text(encoding="utf-8").splitlines())
        if CHECKPOINT_PATH.exists()
        else 0
    )

    print(f"Accepted events: {accepted_count}")
    print(f"DLQ events: {dlq_count}")
    print(f"Checkpointed fingerprints: {checkpoint_count}")


def build_bad_event() -> dict:
    """
    Create an invalid event that should be routed to DLQ.
    """
    event = generate_weather_event()
    event.pop("country")
    event["retry_count"] = 5

    return event


def run_demo() -> None:
    reset_demo_outputs()

    print_section("1. Generate weather events")
    write_weather_events(
        output_path=INPUT_PATH,
        event_count=5,
    )
    print(f"Wrote input events to {INPUT_PATH}")

    print_section("2. Process normal event flow")
    counts = process_weather_events_file(
        input_path=INPUT_PATH,
        accepted_path=ACCEPTED_PATH,
        checkpoint_path=CHECKPOINT_PATH,
        dlq_path=DLQ_PATH,
    )
    print(counts)
    print_counts()

    print_section("3. Prove duplicate protection")
    first_event = read_jsonl(INPUT_PATH)[0]
    duplicate_status = process_weather_event(
        event=first_event,
        accepted_path=ACCEPTED_PATH,
        checkpoint_path=CHECKPOINT_PATH,
        dlq_path=DLQ_PATH,
    )
    print(f"Duplicate event status: {duplicate_status}")
    print_counts()

    print_section("4. Route malformed event to DLQ")
    bad_event = build_bad_event()
    dlq_status = process_weather_event(
        event=bad_event,
        accepted_path=ACCEPTED_PATH,
        checkpoint_path=CHECKPOINT_PATH,
        dlq_path=DLQ_PATH,
    )
    print(f"Malformed event status: {dlq_status}")
    print_counts()

    print_section("5. Simulate network failure and retry")
    outage_event = generate_weather_event()
    os.environ["SIMULATE_NETWORK_FAILURE"] = "true"
    retry_status = process_weather_event(
        event=outage_event,
        accepted_path=ACCEPTED_PATH,
        checkpoint_path=CHECKPOINT_PATH,
        dlq_path=DLQ_PATH,
    )
    print(f"Outage event status: {retry_status}")

    print_section("6. Restore connectivity and recover")
    os.environ["SIMULATE_NETWORK_FAILURE"] = "false"
    recovery_status = process_weather_event(
        event=outage_event,
        accepted_path=ACCEPTED_PATH,
        checkpoint_path=CHECKPOINT_PATH,
        dlq_path=DLQ_PATH,
    )
    print(f"Recovered event status: {recovery_status}")
    print_counts()

    print_section("Demo outputs")
    print(f"Input: {INPUT_PATH}")
    print(f"Accepted: {ACCEPTED_PATH}")
    print(f"DLQ: {DLQ_PATH}")
    print(f"Checkpoints: {CHECKPOINT_PATH}")


if __name__ == "__main__":
    run_demo()
