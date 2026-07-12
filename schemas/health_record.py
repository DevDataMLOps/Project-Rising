import pandera.pandas as pa
from pandera.typing import Series


VALID_ASEAN_COUNTRIES = [
    "Brunei",
    "Cambodia",
    "Indonesia",
    "Laos",
    "Malaysia",
    "Myanmar",
    "Philippines",
    "Singapore",
    "Thailand",
    "Timor-Leste",
    "Vietnam",
]


class HealthRecordSchema(pa.DataFrameModel):
    country: Series[str] = pa.Field(isin=VALID_ASEAN_COUNTRIES)
    year: Series[int] = pa.Field(ge=1900, le=2100)
    indicator: Series[str] = pa.Field(str_length={"min_value": 1})
    value: Series[float] = pa.Field(nullable=False)

    class Config:
        strict = False
        coerce = True
