from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def build_dlq_record(
    original_payload: dict,
    error: Exception,
    retry_count: int,
    source_topic: str,
) -> dict:
    """
    Build a dead-letter event with enough context for replay.
    """
    return {
        "original_payload": original_payload,
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "retry_count": retry_count,
        "failed_at": datetime.now(timezone.utc).isoformat(),
        "source_topic": source_topic,
    }


def write_dlq_record(
    dlq_record: dict,
    output_path: str | Path,
) -> Path:
    """
    Append one dead-letter event to a JSONL file.
    """
    path = Path(output_path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "a",
        encoding="utf-8",
    ) as file:
        file.write(json.dumps(dlq_record) + "\n")

    return path
