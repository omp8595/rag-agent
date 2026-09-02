"""Audit log — design doc section 5: "every Context Package is logged with
request, scope, and the lineage of every returned fact."

Appends one JSON line per Context Package to a file (so the week-6 demo
can show a real audit trail) and keeps an in-memory copy for tests and for
`explain_last()` style inspection without re-parsing the file.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "context_layer_audit.log"


class AuditLog:
    def __init__(self, path: Path = DEFAULT_LOG_PATH):
        self.path = path
        self.entries: list[dict] = []

    def record(self, *, request: dict, scope: dict, context_package: dict) -> dict:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request": request,
            "scope_applied": scope,
            "lineage_id": context_package.get("lineage_id"),
            "fact_count": len(context_package.get("facts", [])),
            "excluded": context_package.get("excluded", []),
        }
        self.entries.append(entry)
        with self.path.open("a") as f:
            f.write(json.dumps(entry) + "\n")
        return entry
