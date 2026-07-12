import pandera.pandas as pa
from pandera.typing import Series

from schemas.health_record import VALID_ASEAN_COUNTRIES


class WeatherEventSchema(pa.DataFrameModel):
    event_id: Series[str] = pa.Field(str_length={"min_value": 1})
    station_id: Series[str] = pa.Field(str_matches=r"^[A-Z]{2}-[A-Z]{3}-\d{2}$")
    country: Series[str] = pa.Field(isin=VALID_ASEAN_COUNTRIES)
    timestamp: Series[str] = pa.Field(str_length={"min_value": 10})
    temperature_c: Series[float] = pa.Field(ge=-20, le=60)
    humidity_pct: Series[float] = pa.Field(ge=0, le=100)
    rainfall_mm: Series[float] = pa.Field(ge=0)

    class Config:
        strict = True
        coerce = True
