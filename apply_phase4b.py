"""Safely register Project RISING Phase 4B in the existing FastAPI application."""

from __future__ import annotations

import py_compile
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN_PATH = ROOT / "main.py"
CONFIG_PATH = ROOT / "api" / "config.py"
REQUIREMENTS_PATH = ROOT / "requirements.txt"
IMPORT_LINE = "from api.routers.ml import router as ml_router"
INCLUDE_LINE = "app.include_router(ml_router)"


def ensure_no_conflict_markers(text: str, path: Path) -> None:
    markers = ("<<<<<<<", "=======", ">>>>>>>")
    if any(marker in text for marker in markers):
        raise RuntimeError(f"Git conflict markers remain in {path}")


def update_main() -> None:
    if not MAIN_PATH.exists():
        raise FileNotFoundError(f"main.py not found: {MAIN_PATH}")
    source = MAIN_PATH.read_text(encoding="utf-8")
    ensure_no_conflict_markers(source, MAIN_PATH)
    backup = MAIN_PATH.with_name("main.py.phase4b-backup")
    if not backup.exists():
        shutil.copy2(MAIN_PATH, backup)

    if IMPORT_LINE not in source:
        anchor = "app = FastAPI("
        if anchor not in source:
            raise RuntimeError("Could not locate 'app = FastAPI(' in main.py")
        source = source.replace(anchor, f"{IMPORT_LINE}\n\n{anchor}", 1)

    if INCLUDE_LINE not in source:
        root_match = re.search(r"(?m)^@app\.get\([\"\']/[\"\']", source)
        if root_match is None:
            raise RuntimeError("Could not locate the root endpoint in main.py")
        insertion = f"# Phase 4B trained ML endpoints\n{INCLUDE_LINE}\n\n"
        source = source[: root_match.start()] + insertion + source[root_match.start() :]

    MAIN_PATH.write_text(source, encoding="utf-8")
    py_compile.compile(str(MAIN_PATH), doraise=True)


def update_api_version() -> None:
    if not CONFIG_PATH.exists():
        return
    source = CONFIG_PATH.read_text(encoding="utf-8")
    ensure_no_conflict_markers(source, CONFIG_PATH)
    updated, count = re.subn(
        r'API_VERSION\s*=\s*["\'][^"\']+["\']',
        'API_VERSION = "4.0.0"',
        source,
        count=1,
    )
    if count:
        CONFIG_PATH.write_text(updated, encoding="utf-8")


def update_requirements() -> None:
    if not REQUIREMENTS_PATH.exists():
        return
    lines = REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
    normalized = [line.strip().casefold() for line in lines]
    additions: list[str] = []
    if not any(line.startswith("scikit-learn") for line in normalized):
        additions.append("scikit-learn>=1.4,<2")
    if not any(line.startswith("joblib") for line in normalized):
        additions.append("joblib>=1.3,<2")
    if additions:
        REQUIREMENTS_PATH.write_text(
            "\n".join(lines + additions) + "\n", encoding="utf-8"
        )


def main() -> None:
    update_main()
    update_api_version()
    update_requirements()
    print("Phase 4B router registered successfully.")
    print("Backup created at main.py.phase4b-backup")
    print("Next commands:")
    print("  python -m ml.train_all")
    print("  python -m pytest tests/test_phase4b_ml.py -v")
    print("  python -m pytest --cache-clear")
    print("  python -m uvicorn main:app --reload")


if __name__ == "__main__":
    main()
