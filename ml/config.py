"""Configuration for Project RISING Phase 4B models."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "asean_health_indicators.csv"
DEFAULT_MODEL_DIR = PROJECT_ROOT / "models" / "phase4b"


def health_data_path() -> Path:
    """Return the configured processed health dataset path."""
    return Path(os.getenv("RISING_HEALTH_DATA_PATH", str(DEFAULT_DATA_PATH))).resolve()


def model_dir() -> Path:
    """Return the configured Phase 4B model artifact directory."""
    return Path(os.getenv("RISING_MODEL_DIR", str(DEFAULT_MODEL_DIR))).resolve()
