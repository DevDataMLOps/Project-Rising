from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import Engine, text
from sqlalchemy.exc import OperationalError

from warehouse.db import get_engine


WEATHER_SOURCE_NAME = "weather-events"
ACCEPTED_QUALITY_STATUS = "accepted"


def parse_event_timestamp(
    timestamp: str,
) -> datetime:
    """
    Parse an ISO timestamp from a weather event.
    """
    normalized_timestamp = timestamp.replace("Z", "+00:00")

    return datetime.fromisoformat(normalized_timestamp)


def date_key_from_timestamp(
    timestamp: str,
) -> int:
    """
    Convert a timestamp into a YYYYMMDD date key.
    """
    observed_at = parse_event_timestamp(timestamp)

    return int(observed_at.strftime("%Y%m%d"))


def upsert_country(
    connection,
    country_name: str,
) -> int:
    result = connection.execute(
        text(
            """
            INSERT INTO dim_country (country_name)
            VALUES (:country_name)
            ON CONFLICT (country_name)
            DO UPDATE SET country_name = EXCLUDED.country_name
            RETURNING country_key
            """
        ),
        {"country_name": country_name},
    )

    return int(result.scalar_one())


def upsert_source(
    connection,
    source_name: str = WEATHER_SOURCE_NAME,
    source_type: str = "stream",
) -> int:
    result = connection.execute(
        text(
            """
            INSERT INTO dim_source (source_name, source_type)
            VALUES (:source_name, :source_type)
            ON CONFLICT (source_name)
            DO UPDATE SET source_type = EXCLUDED.source_type
            RETURNING source_key
            """
        ),
        {
            "source_name": source_name,
            "source_type": source_type,
        },
    )

    return int(result.scalar_one())


def upsert_quality_status(
    connection,
    quality_status: str = ACCEPTED_QUALITY_STATUS,
) -> int:
    result = connection.execute(
        text(
            """
            INSERT INTO dim_quality_status (quality_status, description)
            VALUES (:quality_status, :description)
            ON CONFLICT (quality_status)
            DO UPDATE SET description = EXCLUDED.description
            RETURNING quality_status_key
            """
        ),
        {
            "quality_status": quality_status,
            "description": "Record passed schema validation and was loaded.",
        },
    )

    return int(result.scalar_one())


def upsert_station(
    connection,
    station_id: str,
    country_key: int,
) -> int:
    result = connection.execute(
        text(
            """
            INSERT INTO dim_station (station_id, country_key)
            VALUES (:station_id, :country_key)
            ON CONFLICT (station_id)
            DO UPDATE SET country_key = EXCLUDED.country_key
            RETURNING station_key
            """
        ),
        {
            "station_id": station_id,
            "country_key": country_key,
        },
    )

    return int(result.scalar_one())


def upsert_date(
    connection,
    observed_at: datetime,
) -> int:
    date_key = int(observed_at.strftime("%Y%m%d"))
    full_date = observed_at.date()
    quarter = ((observed_at.month - 1) // 3) + 1

    result = connection.execute(
        text(
            """
            INSERT INTO dim_date (
                date_key,
                full_date,
                year,
                month,
                day,
                quarter
            )
            VALUES (
                :date_key,
                :full_date,
                :year,
                :month,
                :day,
                :quarter
            )
            ON CONFLICT (date_key)
            DO UPDATE SET full_date = EXCLUDED.full_date
            RETURNING date_key
            """
        ),
        {
            "date_key": date_key,
            "full_date": full_date,
            "year": observed_at.year,
            "month": observed_at.month,
            "day": observed_at.day,
            "quarter": quarter,
        },
    )

    return int(result.scalar_one())


def load_weather_event(
    connection,
    event: dict,
) -> bool:
    """
    Load one weather event into warehouse dimensions and fact table.
    """
    observed_at = parse_event_timestamp(event["timestamp"])

    country_key = upsert_country(
        connection=connection,
        country_name=event["country"],
    )
    source_key = upsert_source(connection)
    quality_status_key = upsert_quality_status(connection)
    station_key = upsert_station(
        connection=connection,
        station_id=event["station_id"],
        country_key=country_key,
    )
    date_key = upsert_date(
        connection=connection,
        observed_at=observed_at,
    )

    result = connection.execute(
        text(
            """
            INSERT INTO fact_weather_observation (
                country_key,
                station_key,
                date_key,
                source_key,
                quality_status_key,
                event_id,
                observed_at,
                temperature_c,
                humidity_pct,
                rainfall_mm
            )
            VALUES (
                :country_key,
                :station_key,
                :date_key,
                :source_key,
                :quality_status_key,
                :event_id,
                :observed_at,
                :temperature_c,
                :humidity_pct,
                :rainfall_mm
            )
            ON CONFLICT (event_id) DO NOTHING
            """
        ),
        {
            "country_key": country_key,
            "station_key": station_key,
            "date_key": date_key,
            "source_key": source_key,
            "quality_status_key": quality_status_key,
            "event_id": event["event_id"],
            "observed_at": observed_at,
            "temperature_c": event["temperature_c"],
            "humidity_pct": event["humidity_pct"],
            "rainfall_mm": event["rainfall_mm"],
        },
    )

    return result.rowcount == 1


def iter_jsonl_events(
    input_path: str | Path,
) -> list[dict]:
    """
    Read weather events from a JSONL file.
    """
    path = Path(input_path)

    if not path.exists():
        return []

    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_weather_events_jsonl(
    input_path: str | Path,
    engine: Engine | None = None,
) -> dict[str, int]:
    """
    Load accepted weather JSONL events into PostgreSQL.
    """
    events = iter_jsonl_events(input_path)
    warehouse_engine = engine or get_engine()

    counts = {
        "input": len(events),
        "inserted": 0,
        "duplicates": 0,
    }

    try:
        with warehouse_engine.begin() as connection:
            for event in events:
                inserted = load_weather_event(
                    connection=connection,
                    event=event,
                )

                if inserted:
                    counts["inserted"] += 1
                else:
                    counts["duplicates"] += 1
    except OperationalError as exc:
        raise RuntimeError(
            "Could not connect to the PostgreSQL warehouse. "
            "Confirm Docker Postgres is running and that DATABASE_URL matches "
            "the credentials in docker-compose.yml. If the Docker volume was "
            "created with old credentials, recreate it with: "
            "docker compose down -v; docker compose up -d postgres"
        ) from exc

    return counts
