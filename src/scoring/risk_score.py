"""Risk scoring engine for scan reports."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List


class RiskScorer:
    """Combines findings into a simple 0-100 risk score."""

    def build_report(
        self,
        scan_type: str,
        target: str,
        findings: List[Dict[str, Any]],
        metadata: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        risk_score = self.calculate_score(findings)
        risk_level = self.level_for_score(risk_score)
        actionable_findings = [f for f in findings if f.get("severity") != "info"]
        report = {
            "scan_id": str(uuid.uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "scan_type": scan_type,
            "target": target,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "summary": self.summary_for(risk_level, actionable_findings),
            "recommended_action": self.recommended_action(risk_level),
            "findings": findings,
            "metadata": metadata or {},
            "disclaimer": "This is a defensive heuristic report, not a guarantee of safety or maliciousness.",
        }
        return report

    def calculate_score(self, findings: List[Dict[str, Any]]) -> int:
        total = 0
        severity_bonus = {"critical": 12, "high": 8, "medium": 4, "low": 1, "info": 0}
        for finding in findings:
            total += int(finding.get("score", 0))
            total += severity_bonus.get(str(finding.get("severity", "info")).lower(), 0)
        # Reduce score inflation from many low-value findings, but keep serious findings high.
        critical_or_high = sum(1 for f in findings if f.get("severity") in {"critical", "high"})
        if critical_or_high >= 2:
            total += 10
        return max(0, min(100, total))

    def level_for_score(self, score: int) -> str:
        if score <= 20:
            return "Safe"
        if score <= 50:
            return "Suspicious"
        if score <= 75:
            return "High Risk"
        return "Dangerous"

    def summary_for(self, risk_level: str, findings: List[Dict[str, Any]]) -> str:
        if not findings:
            return "No obvious risk indicators were found by local heuristics. Continue using normal caution."
        titles = [str(f.get("title", f.get("type", "finding"))) for f in findings[:3]]
        return f"{risk_level}: detected {len(findings)} risk indicator(s), including: " + "; ".join(titles) + "."

    def recommended_action(self, risk_level: str) -> str:
        return {
            "Safe": "No obvious risk found. Still verify the sender/source before trusting it.",
            "Suspicious": "Do not enter passwords or personal details. Verify the source through a trusted channel.",
            "High Risk": "Avoid opening or downloading. Ask a trusted technical person to review it first.",
            "Dangerous": "Do not open, execute, or share it. Delete/quarantine it and report it if it came from a message or email.",
        }[risk_level]
