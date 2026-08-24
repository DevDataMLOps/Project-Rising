from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from api.config import HEALTH_DATA_PATH, INDICATOR_METADATA_PATH


class DataUnavailableError(RuntimeError):
    """Raised when the processed ETL output is not available."""


def _clean_records(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    clean = dataframe.astype(object).where(pd.notna(dataframe), None)
    return clean.to_dict(orient="records")


class HealthRepository:
    def __init__(
        self,
        health_path: Path = HEALTH_DATA_PATH,
        metadata_path: Path = INDICATOR_METADATA_PATH,
    ) -> None:
        self.health_path = health_path
        self.metadata_path = metadata_path

    @lru_cache(maxsize=1)
    def load_health_data(self) -> pd.DataFrame:
        if not self.health_path.exists():
            raise DataUnavailableError(
                f"Processed health data was not found at {self.health_path}. "
                "Run: py -m pipelines.run_etl"
            )

        dataframe = pd.read_csv(self.health_path)
        required = {"country", "year", "indicator", "value"}
        missing = required.difference(dataframe.columns)
        if missing:
            raise DataUnavailableError(
                f"Processed health data is missing columns: {sorted(missing)}"
            )

        dataframe = dataframe.copy()
        dataframe["country"] = dataframe["country"].astype(str).str.strip()
        dataframe["indicator"] = dataframe["indicator"].astype(str).str.strip()
        dataframe["year"] = pd.to_numeric(dataframe["year"], errors="coerce")
        dataframe["value"] = pd.to_numeric(dataframe["value"], errors="coerce")
        dataframe = dataframe.dropna(subset=["country", "year", "indicator", "value"])
        dataframe["year"] = dataframe["year"].astype(int)
        return dataframe.sort_values(["country", "indicator", "year"]).reset_index(drop=True)

    @lru_cache(maxsize=1)
    def load_metadata(self) -> pd.DataFrame:
        if not self.metadata_path.exists():
            return pd.DataFrame(columns=["indicator", "indicator_label", "description"])
        return pd.read_csv(self.metadata_path)

    def clear_cache(self) -> None:
        self.load_health_data.cache_clear()
        self.load_metadata.cache_clear()

    def countries(self) -> list[str]:
        return sorted(self.load_health_data()["country"].dropna().unique().tolist())

    def indicators(self) -> list[str]:
        return sorted(self.load_health_data()["indicator"].dropna().unique().tolist())

    def resolve_country(self, country: str) -> str:
        match = {name.casefold(): name for name in self.countries()}.get(country.strip().casefold())
        if not match:
            raise KeyError(country)
        return match

    def resolve_indicator(self, indicator: str) -> str:
        match = {
            name.casefold(): name for name in self.indicators()
        }.get(indicator.strip().casefold())
        if not match:
            raise KeyError(indicator)
        return match

    def filter_records(
        self,
        *,
        country: str | None = None,
        indicator: str | None = None,
        year: int | None = None,
        sex: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[int, list[dict[str, Any]]]:
        dataframe = self.load_health_data()

        if country:
            dataframe = dataframe[
                dataframe["country"].str.casefold() == country.strip().casefold()
            ]
        if indicator:
            dataframe = dataframe[
                dataframe["indicator"].str.casefold() == indicator.strip().casefold()
            ]
        if year is not None:
            dataframe = dataframe[dataframe["year"] == year]
        if sex and "sex" in dataframe.columns:
            dataframe = dataframe[
                dataframe["sex"].fillna("").astype(str).str.casefold()
                == sex.strip().casefold()
            ]

        dataframe = dataframe.sort_values(["country", "indicator", "year"])
        total = len(dataframe)
        page = dataframe.iloc[offset : offset + limit]
        return total, _clean_records(page)

    def latest_country_values(self, country: str) -> pd.DataFrame:
        resolved = self.resolve_country(country)
        dataframe = self.load_health_data()
        country_data = dataframe[dataframe["country"] == resolved].copy()
        dimensions = ["indicator"]
        for optional in ("sub_indicator", "sex"):
            if optional in country_data.columns:
                dimensions.append(optional)
        return (
            country_data.sort_values("year")
            .groupby(dimensions, dropna=False, as_index=False)
            .tail(1)
            .sort_values("indicator")
            .reset_index(drop=True)
        )

    def latest_indicator_by_country(self, indicator: str) -> pd.DataFrame:
        resolved = self.resolve_indicator(indicator)
        dataframe = self.load_health_data()
        subset = dataframe[dataframe["indicator"] == resolved].copy()
        return (
            subset.sort_values("year")
            .groupby("country", as_index=False)
            .tail(1)
            .sort_values("country")
            .reset_index(drop=True)
        )

    def trend(self, country: str, indicator: str) -> pd.DataFrame:
        resolved_country = self.resolve_country(country)
        resolved_indicator = self.resolve_indicator(indicator)
        dataframe = self.load_health_data()
        result = dataframe[
            (dataframe["country"] == resolved_country)
            & (dataframe["indicator"] == resolved_indicator)
        ].copy()
        return result.sort_values("year").reset_index(drop=True)

    def metadata_records(self) -> list[dict[str, Any]]:
        return _clean_records(self.load_metadata())


repository = HealthRepository()
