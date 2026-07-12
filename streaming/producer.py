from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path


STATIONS = [
    ("TH-BKK-01", "Thailand"),
    ("ID-JKT-01", "Indonesia"),
    ("PH-MNL-01", "Philippines"),
    ("VN-HAN-01", "Vietnam"),
]


def generate_weather_event() -> dict:
    """
    Generate one simulated weather event.
    """
    station_id, country = random.choice(STATIONS)

    return {
        "event_id": str(uuid.uuid4()),
        "station_id": station_id,
        "country": country,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature_c": round(random.uniform(24.0, 39.0), 1),
        "humidity_pct": round(random.uniform(50.0, 95.0), 1),
        "rainfall_mm": round(random.uniform(0.0, 80.0), 1),
    }


def write_weather_events(
    output_path: str | Path,
    event_count: int = 10,
) -> Path:
    """
    Write simulated weather events to a JSONL landing file.
    """
    path = Path(output_path)
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        for _ in range(event_count):
            file.write(json.dumps(generate_weather_event()) + "\n")

    return path


if __name__ == "__main__":
    write_weather_events(
        output_path="data/streaming/weather_events.jsonl",
        event_count=25,
    )
