from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pandas as pd
import pandera.pandas as pa

from schemas.weather_event import WeatherEventSchema
from streaming.dlq_handler import build_dlq_record, write_dlq_record
from streaming.retry_handler import increment_retry_count, should_retry


class SimulatedNetworkError(RuntimeError):
    """Raised when local outage simulation is enabled."""


def event_fingerprint(
    event: dict,
) -> str:
    """
    Generate a stable fingerprint for idempotent event processing.
    """
    fingerprint_source = "|".join(
        [
            str(event.get("event_id", "")),
            str(event.get("station_id", "")),
            str(event.get("country", "")),
            str(event.get("timestamp", "")),
        ]
    )

    return hashlib.sha256(
        fingerprint_source.encode("utf-8")
    ).hexdigest()


def load_processed_fingerprints(
    checkpoint_path: str | Path,
) -> set[str]:
    """
    Load processed event fingerprints from a checkpoint file.
    """
    path = Path(checkpoint_path)

    if not path.exists():
        return set()

    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def append_checkpoint(
    checkpoint_path: str | Path,
    fingerprint: str,
) -> None:
    """
    Persist one processed event fingerprint.
    """
    path = Path(checkpoint_path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open("a", encoding="utf-8") as file:
        file.write(f"{fingerprint}\n")


def validate_weather_event(
    event: dict,
) -> dict:
    """
    Validate one weather event using the Pandera contract.
    """
    contract_payload = {
        key: value
        for key, value in event.items()
        if key not in {"retry_count"}
    }

    dataframe = pd.DataFrame([contract_payload])
    validated = WeatherEventSchema.validate(dataframe)

    return validated.iloc[0].to_dict()


def append_weather_event(
    event: dict,
    output_path: str | Path,
) -> Path:
    """
    Append one accepted weather event to local JSONL storage.
    """
    if os.getenv("SIMULATE_NETWORK_FAILURE", "").lower() == "true":
        raise SimulatedNetworkError(
            "Network/database write failed during outage simulation."
        )

    path = Path(output_path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event) + "\n")

    return path


def process_weather_event(
    event: dict,
    accepted_path: str | Path,
    checkpoint_path: str | Path,
    dlq_path: str | Path,
    source_topic: str = "weather-events",
    max_retries: int = 5,
) -> str:
    """
    Validate, deduplicate, and persist one weather event.
    """
    retry_count = int(event.get("retry_count", 0))

    try:
        validated_event = validate_weather_event(event)
        fingerprint = event_fingerprint(validated_event)
        processed_fingerprints = load_processed_fingerprints(
            checkpoint_path
        )

        if fingerprint in processed_fingerprints:
            return "duplicate"

        append_weather_event(
            event=validated_event,
            output_path=accepted_path,
        )
        append_checkpoint(
            checkpoint_path=checkpoint_path,
            fingerprint=fingerprint,
        )

        return "accepted"

    except (pa.errors.SchemaError, SimulatedNetworkError, ValueError) as error:
        if should_retry(
            retry_count=retry_count,
            max_retries=max_retries,
        ):
            return "retry"

        dlq_record = build_dlq_record(
            original_payload=event,
            error=error,
            retry_count=retry_count,
            source_topic=source_topic,
        )
        write_dlq_record(
            dlq_record=dlq_record,
            output_path=dlq_path,
        )

        return "dlq"


def process_weather_events_file(
    input_path: str | Path,
    accepted_path: str | Path,
    checkpoint_path: str | Path,
    dlq_path: str | Path,
) -> dict[str, int]:
    """
    Process a JSONL file of weather events.
    """
    counts = {
        "accepted": 0,
        "duplicate": 0,
        "retry": 0,
        "dlq": 0,
    }

    for line in Path(input_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        event = json.loads(line)
        status = process_weather_event(
            event=event,
            accepted_path=accepted_path,
            checkpoint_path=checkpoint_path,
            dlq_path=dlq_path,
        )
        counts[status] += 1

    return counts


def retry_event(
    event: dict,
) -> dict:
    """
    Prepare a failed event for a retry queue.
    """
    return increment_retry_count(event)
