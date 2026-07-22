"""Small durable JSON store for Phase 4 alerts.

The MVP intentionally avoids adding a database requirement. Alerts are stored in
``data/runtime/phase4_alerts.json`` using atomic replacement so local demos,
Render deployments, and tests can all use the same interface.
"""

from __future__ import annotations

import json
import os
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORE_PATH = PROJECT_ROOT / "data" / "runtime" / "phase4_alerts.json"
_LOCK = threading.RLock()


def _store_path() -> Path:
    override = os.getenv("RISING_ALERT_STORE")
    return Path(override).expanduser().resolve() if override else DEFAULT_STORE_PATH


def _read_unlocked(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return payload if isinstance(payload, list) else []


def list_alerts() -> list[dict[str, Any]]:
    """Return a defensive copy of stored alerts."""

    path = _store_path()
    with _LOCK:
        return deepcopy(_read_unlocked(path))


def save_alerts(alerts: list[dict[str, Any]]) -> None:
    """Persist all alerts with an atomic file replacement."""

    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with _LOCK:
        temporary.write_text(
            json.dumps(alerts, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(path)


def upsert_alert(alert: dict[str, Any]) -> dict[str, Any]:
    """Create or update an alert using its deduplication key."""

    path = _store_path()
    with _LOCK:
        alerts = _read_unlocked(path)
        key = alert["dedup_key"]
        existing_index = next(
            (
                index
                for index, item in enumerate(alerts)
                if item.get("dedup_key") == key
                and item.get("status") in {"open", "acknowledged"}
            ),
            None,
        )
        if existing_index is None:
            alerts.append(alert)
            stored = alert
        else:
            previous = alerts[existing_index]
            merged = {
                **previous,
                **alert,
                "id": previous["id"],
                "created_at": previous["created_at"],
                "occurrences": int(previous.get("occurrences", 1)) + 1,
                "status": (
                    "resolved"
                    if alert.get("status") == "resolved"
                    else previous.get("status", "open")
                ),
                "acknowledgement": previous.get("acknowledgement"),
            }
            alerts[existing_index] = merged
            stored = merged

        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(alerts, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(path)
        return deepcopy(stored)


def update_alert(alert_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update one alert by ID and return the new record."""

    path = _store_path()
    with _LOCK:
        alerts = _read_unlocked(path)
        for index, alert in enumerate(alerts):
            if alert.get("id") != alert_id:
                continue
            alerts[index] = {**alert, **updates}
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + ".tmp")
            temporary.write_text(
                json.dumps(alerts, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            temporary.replace(path)
            return deepcopy(alerts[index])
    return None


def clear_alerts() -> None:
    """Clear the store. Primarily used by automated tests and local demos."""

    save_alerts([])
