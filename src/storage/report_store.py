"""Simple JSON report storage for local development."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Dict


class ReportStore:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()
        self._memory: Dict[str, Any] = {}
        self._persistent = True
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.exists():
                self.path.write_text("{}", encoding="utf-8")
        except OSError:
            # Serverless filesystems may be read-only. Authenticated reports should use DATABASE_URL.
            self._persistent = False

    def _read_all(self) -> Dict[str, Any]:
        if not self._persistent:
            return dict(self._memory)
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def save(self, report: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            data = self._read_all()
            data[report["scan_id"]] = report
            if self._persistent:
                self.path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
            self._memory[report["scan_id"]] = report
        return report

    def get(self, scan_id: str) -> Dict[str, Any] | None:
        with self._lock:
            return self._read_all().get(scan_id) or self._memory.get(scan_id)
