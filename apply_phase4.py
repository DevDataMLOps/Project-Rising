"""Safely register the Phase 4 operations router in Project RISING main.py."""

from __future__ import annotations

import ast
import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
IMPORT_LINE = "from api.routes.operations import router as operations_router"
ROUTER_BLOCK = '''\napp.include_router(\n    operations_router,\n    prefix="/api/v1",\n)\n'''


def main() -> None:
    if not MAIN.exists():
        raise SystemExit(f"main.py was not found at {MAIN}")

    content = MAIN.read_text(encoding="utf-8")
    if any(marker in content for marker in ("<<<<<<<", "=======", ">>>>>>>")):
        raise SystemExit("main.py still contains Git conflict markers. Resolve them first.")

    backup = MAIN.with_name(
        f"main.py.phase4-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    shutil.copy2(MAIN, backup)

    if IMPORT_LINE not in content:
        import_anchor = "from api.routes.risk import router as risk_router"
        if import_anchor in content:
            content = content.replace(import_anchor, f"{import_anchor}\n{IMPORT_LINE}", 1)
        else:
            cors_anchor = "from fastapi.middleware.cors import CORSMiddleware"
            if cors_anchor not in content:
                raise SystemExit("Could not find a safe import insertion point in main.py")
            content = content.replace(cors_anchor, f"{cors_anchor}\n\n{IMPORT_LINE}", 1)

    if "app.include_router(\n    operations_router," not in content:
        endpoint_anchor = '@app.get("/", tags=["System"])'
        if endpoint_anchor not in content:
            raise SystemExit("Could not find the root endpoint insertion point in main.py")
        content = content.replace(endpoint_anchor, f"{ROUTER_BLOCK}\n{endpoint_anchor}", 1)

    content = content.replace('version="2.0.0"', 'version="3.0.0"', 1)
    content = content.replace('"version": "2.0.0"', '"version": "3.0.0"', 1)

    ast.parse(content)
    MAIN.write_text(content, encoding="utf-8")
    print(f"Phase 4 router registered successfully. Backup: {backup.name}")


if __name__ == "__main__":
    main()
