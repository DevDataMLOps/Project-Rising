import pandas as pd
import pandera.pandas as pa
import pytest

from schemas.health_record import HealthRecordSchema
from schemas.weather_event import WeatherEventSchema
from streaming.consumer import validate_weather_event


def test_health_record_schema_accepts_valid_records():
    dataframe = pd.DataFrame(
        {
            "country": ["Brunei"],
            "year": [2020],
            "indicator": ["crude_birth_ratio"],
            "value": [12.5],
            "unit": ["per 1000 population"],
        }
    )

    validated = HealthRecordSchema.validate(dataframe)

    assert validated.loc[0, "country"] == "Brunei"


def test_health_record_schema_rejects_unknown_country():
    dataframe = pd.DataFrame(
        {
            "country": ["Atlantis"],
            "year": [2020],
            "indicator": ["crude_birth_ratio"],
            "value": [12.5],
        }
    )

    with pytest.raises(pa.errors.SchemaError):
        HealthRecordSchema.validate(dataframe)


def test_weather_event_schema_accepts_valid_event():
    event = {
        "event_id": "event-1",
        "station_id": "TH-BKK-01",
        "country": "Thailand",
        "timestamp": "2026-06-21T14:05:00Z",
        "temperature_c": 34.2,
        "humidity_pct": 81.0,
        "rainfall_mm": 12.4,
    }

    validated_event = validate_weather_event(event)

    assert validated_event["event_id"] == "event-1"
    assert validated_event["country"] == "Thailand"


def test_weather_event_schema_rejects_malformed_event():
    dataframe = pd.DataFrame(
        {
            "event_id": ["event-1"],
            "station_id": ["bad-station"],
            "country": ["Thailand"],
            "timestamp": ["2026-06-21T14:05:00Z"],
            "temperature_c": [34.2],
            "humidity_pct": [101.0],
            "rainfall_mm": [12.4],
        }
    )

    with pytest.raises(pa.errors.SchemaError):
        WeatherEventSchema.validate(dataframe)
