"""Model registry helpers for Phase 4B."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REGISTRY_FILENAME = "registry.json"
TRAINING_REPORT_FILENAME = "training_report.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Model metadata not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    temporary.replace(path)


def load_registry(model_directory: Path) -> dict[str, Any]:
    return read_json(Path(model_directory) / REGISTRY_FILENAME)


def load_training_report(model_directory: Path) -> dict[str, Any]:
    return read_json(Path(model_directory) / TRAINING_REPORT_FILENAME)
