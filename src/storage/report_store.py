"""Simple JSON report storage for local development."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict


class ReportStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def _read_all(self) -> Dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def save(self, report: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            data = self._read_all()
            data[report["scan_id"]] = report
            self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        return report

    def get(self, scan_id: str) -> Dict[str, Any] | None:
        with self._lock:
            return self._read_all().get(scan_id)
