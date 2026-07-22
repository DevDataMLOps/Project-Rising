"""Dataset loading and validation helpers for Phase 4B."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = {"country", "year", "indicator", "value"}


def load_health_data(path: Path) -> pd.DataFrame:
    """Load the long-form ASEAN health dataset and enforce ML-ready types."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Processed health dataset not found: {path}")

    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(
            "Processed health dataset is missing required columns: "
            + ", ".join(sorted(missing))
        )

    clean = frame.loc[:, ["country", "year", "indicator", "value"]].copy()
    clean["country"] = clean["country"].astype(str).str.strip()
    clean["indicator"] = clean["indicator"].astype(str).str.strip()
    clean["year"] = pd.to_numeric(clean["year"], errors="coerce")
    clean["value"] = pd.to_numeric(clean["value"], errors="coerce")
    clean = clean.dropna(subset=["country", "indicator", "year", "value"])
    clean = clean[(clean["country"] != "") & (clean["indicator"] != "")]
    clean["year"] = clean["year"].astype(int)
    clean["value"] = clean["value"].astype(float)
    clean = clean.drop_duplicates(
        subset=["country", "indicator", "year"], keep="last"
    )
    clean = clean.sort_values(["country", "indicator", "year"]).reset_index(drop=True)

    if clean.empty:
        raise ValueError("Processed health dataset contains no usable records.")
    return clean


def dataset_sha256(path: Path) -> str:
    """Return a stable SHA-256 hash for model lineage."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_value(requested: str, values: list[str], label: str) -> str:
    """Resolve a user value case-insensitively while preserving canonical spelling."""
    requested_key = requested.strip().casefold()
    match = next((value for value in values if value.casefold() == requested_key), None)
    if match is None:
        raise KeyError(f"Unknown {label}: {requested}")
    return match


def series_key(country: str, indicator: str) -> str:
    """Create a JSON-safe lookup key for a country/indicator series."""
    return f"{country}|||{indicator}"
