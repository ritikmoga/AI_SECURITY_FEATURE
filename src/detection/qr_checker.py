"""QR text scanner.

For this backend MVP, QR images should be decoded on the client or by a trusted QR
library before sending the decoded text here. The backend then analyzes the content.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List

from src.config import AppConfig
from src.detection.url_checker import URLChecker


@dataclass(frozen=True)
class Finding:
    type: str
    severity: str
    title: str
    description: str
    evidence: Dict[str, Any]
    score: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class QRChecker:
    def __init__(self, config: AppConfig, *, url_checker: URLChecker):
        self.config = config
        self.url_checker = url_checker

    def analyze_text(self, text: str) -> List[Dict[str, Any]]:
        findings: List[Finding] = []
        normalized = text.strip()

        if re.match(r"^https?://", normalized, flags=re.IGNORECASE):
            return self.url_checker.analyze_url(normalized)

        embedded_urls = self.url_checker.extract_urls(normalized)
        if embedded_urls:
            url_findings: List[Dict[str, Any]] = []
            for url in embedded_urls:
                url_findings.extend(self.url_checker.analyze_url(url))
            findings.append(Finding(
                type="qr_embedded_url", severity="medium", title="QR contains embedded URL",
                description="The QR text includes at least one link. Review the URL scan findings before opening it.",
                evidence={"url_count": len(embedded_urls)}, score=12,
            ))
            return [f.to_dict() for f in findings] + url_findings

        if normalized.lower().startswith(("upi://", "mailto:", "tel:", "sms:", "whatsapp://")):
            findings.append(Finding(
                type="qr_action_link", severity="medium", title="QR triggers an app action",
                description="This QR code can open another app or initiate an action. Confirm the destination before continuing.",
                evidence={"prefix": normalized.split(":", 1)[0]}, score=15,
            ))

        if len(normalized) > 500:
            findings.append(Finding(
                type="qr_long_text", severity="low", title="QR contains long text",
                description="Long QR content can hide tracking data or confusing instructions.",
                evidence={"length": len(normalized)}, score=8,
            ))

        if not findings:
            findings.append(Finding(
                type="no_obvious_qr_risk", severity="info", title="No obvious QR risk found",
                description="No local QR heuristic warning was triggered. This does not guarantee the QR content is safe.",
                evidence={}, score=0,
            ))

        return [finding.to_dict() for finding in findings]
