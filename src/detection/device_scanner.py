"""Consent-based local directory scanner. It never executes files."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config import AppConfig
from src.detection.malware_detector import MalwareDetector
from src.scoring.risk_score import RiskScorer


DEFAULT_EXCLUDED_DIRECTORIES = {".git", ".venv", "venv", "node_modules", "__pycache__", "$recycle.bin", "windows", "program files"}


class DeviceScanner:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.detector = MalwareDetector(config)
        self.scorer = RiskScorer()

    def scan_directory(self, directory: Path, *, max_files: int = 1000, include_hidden: bool = False) -> dict[str, Any]:
        directory = directory.expanduser().resolve()
        if not directory.is_dir():
            raise ValueError("Select an existing directory for the local device scan.")
        findings: list[dict[str, Any]] = []
        scanned = skipped = 0
        max_bytes = self.config.max_file_size_mb * 1024 * 1024
        for path in directory.rglob("*"):
            if scanned >= max_files:
                break
            relative = path.relative_to(directory)
            if not include_hidden and any(part.startswith(".") or part.lower() in DEFAULT_EXCLUDED_DIRECTORIES for part in relative.parts):
                continue
            if not path.is_file():
                continue
            try:
                if path.stat().st_size > max_bytes:
                    skipped += 1; continue
                file_findings, _ = self.detector.analyze_file(path, original_filename=path.name)
                scanned += 1
                for finding in file_findings:
                    if finding.get("severity") != "info":
                        findings.append({**finding, "evidence": {**dict(finding.get("evidence", {})), "path": str(relative)}})
            except (OSError, PermissionError):
                skipped += 1
        if not findings:
            findings = [{"type": "no_obvious_device_risk", "severity": "info", "title": "No obvious local file risk found", "description": "Static checks found no high-confidence warning in the scanned files.", "evidence": {"files_scanned": scanned}, "score": 0}]
        return self.scorer.build_report("file", str(directory), findings[:100], metadata={"mode": "local_directory_scan", "files_scanned": scanned, "files_skipped": skipped, "max_files": max_files, "static_analysis_only": True})
