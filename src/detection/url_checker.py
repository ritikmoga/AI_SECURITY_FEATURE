"""Safe URL analysis module.

This module only performs defensive checks. It does not exploit, attack, or execute
content from URLs. Optional external reputation services can be enabled with API keys.
"""
from __future__ import annotations

import hashlib
import ipaddress
import math
import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List
from urllib.parse import parse_qs, unquote, urlparse

from src.config import AppConfig
from src.services.google_safe_browsing_service import GoogleSafeBrowsingService
from src.services.urlscan_service import UrlscanService
from src.services.virustotal_service import VirusTotalService


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


class URLChecker:
    """Checks URLs for suspicious characteristics and optional reputation hits."""

    SHORTENERS = {
        "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly",
        "cutt.ly", "rebrand.ly", "shorturl.at", "s.id", "rb.gy", "lnkd.in"
    }
    SUSPICIOUS_TLDS = {"tk", "ml", "ga", "cf", "gq", "zip", "mov", "top", "xyz", "click", "cam", "work"}
    BRAND_TARGETS = {
        "paypal": ["paypa1", "pay-pal", "paypal-secure"],
        "google": ["goog1e", "g00gle", "google-login"],
        "amazon": ["amaz0n", "amazon-secure"],
        "microsoft": ["micros0ft", "microsoft-login"],
        "instagram": ["instagrarn", "instagram-login"],
        "whatsapp": ["whats-app", "whatsapp-login"],
    }

    def __init__(self, config: AppConfig):
        self.config = config
        self.google_safe_browsing = GoogleSafeBrowsingService(config)
        self.virustotal = VirusTotalService(config)
        self.urlscan = UrlscanService(config)

    def check(self, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        urls = self.extract_urls(f"{message.get('subject', '')}\n{message.get('body', '')}")
        findings: List[Dict[str, Any]] = []
        for url in urls:
            findings.extend(self.analyze_url(url))
        return findings

    def extract_urls(self, text: str) -> List[str]:
        raw = re.findall(r"https?://[^\s<>'\")]+", text or "", flags=re.IGNORECASE)
        return sorted(set(url.rstrip(".,;!?") for url in raw))

    def analyze_url(self, url: str) -> List[Dict[str, Any]]:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower().strip(".")
        domain_parts = hostname.split(".") if hostname else []
        tld = domain_parts[-1] if domain_parts else ""
        findings: List[Finding] = []

        if parsed.scheme != "https":
            findings.append(Finding(
                type="url_transport", severity="medium", title="URL does not use HTTPS",
                description="The link uses unencrypted HTTP. Sensitive data could be exposed or modified in transit.",
                evidence={"scheme": parsed.scheme}, score=14,
            ))

        if self._is_ip_host(hostname):
            score = 28 if parsed.scheme == "http" else 18
            findings.append(Finding(
                type="ip_based_url", severity="high" if score >= 25 else "medium", title="IP-based URL",
                description="Legitimate services normally use a domain name. Raw IP links are commonly used in scams and temporary infrastructure.",
                evidence={"hostname": hostname}, score=score,
            ))
            if self._is_private_or_local_ip(hostname):
                findings.append(Finding(
                    type="local_network_url", severity="high", title="Local or private network address",
                    description="The URL points to a private/local address. Scanners should not fetch it automatically because of SSRF risk.",
                    evidence={"hostname": hostname}, score=35,
                ))

        if hostname in self.SHORTENERS:
            findings.append(Finding(
                type="shortened_url", severity="medium", title="URL shortener detected",
                description="Short links hide the final destination. Expand and verify before opening.",
                evidence={"hostname": hostname}, score=20,
            ))

        if tld in self.SUSPICIOUS_TLDS:
            findings.append(Finding(
                type="suspicious_tld", severity="medium", title="Risky top-level domain",
                description="This top-level domain has elevated abuse risk and should be checked carefully.",
                evidence={"tld": tld}, score=16,
            ))

        if "@" in urlparse(url).netloc or "@" in parsed.path:
            findings.append(Finding(
                type="credential_confusion", severity="high", title="@ symbol in URL",
                description="The @ symbol can be used to make a URL look like it points to a trusted domain while sending users elsewhere.",
                evidence={"url_preview": self._safe_preview(url)}, score=30,
            ))

        decoded_url = unquote(url)
        if decoded_url != url and any(token in decoded_url.lower() for token in ["http://", "https://", "@"]):
            findings.append(Finding(
                type="encoded_redirect", severity="medium", title="Encoded URL elements",
                description="Encoded redirect-like data was found. Attackers often hide the real target using URL encoding.",
                evidence={"decoded_preview": self._safe_preview(decoded_url)}, score=18,
            ))

        if len(url) > 180:
            findings.append(Finding(
                type="long_url", severity="low", title="Very long URL",
                description="Very long URLs can hide tracking parameters, redirects, or suspicious payload markers.",
                evidence={"length": len(url)}, score=8,
            ))

        if hostname.count("-") >= 3 or len(domain_parts) >= 5:
            findings.append(Finding(
                type="complex_hostname", severity="low", title="Complex hostname",
                description="The hostname has many subdomains or separators, which can be used to imitate trusted services.",
                evidence={"hostname": hostname}, score=10,
            ))

        entropy = self._entropy(hostname.replace(".", ""))
        if entropy > 3.7 and len(hostname) > 18:
            findings.append(Finding(
                type="high_entropy_domain", severity="medium", title="Random-looking domain",
                description="The domain looks unusually random, which can indicate temporary or automated scam infrastructure.",
                evidence={"hostname": hostname, "entropy": round(entropy, 2)}, score=18,
            ))

        for brand, variants in self.BRAND_TARGETS.items():
            if hostname != f"{brand}.com" and any(v in hostname for v in variants):
                findings.append(Finding(
                    type="brand_impersonation", severity="high", title="Possible brand impersonation",
                    description="The domain appears to imitate a trusted brand using lookalike spelling or login wording.",
                    evidence={"brand": brand, "hostname": hostname}, score=34,
                ))
                break

        query = parse_qs(parsed.query)
        redirect_keys = {"url", "u", "redirect", "redirect_url", "next", "target", "to", "continue"}
        if redirect_keys.intersection(query.keys()):
            findings.append(Finding(
                type="redirect_parameter", severity="medium", title="Redirect parameter found",
                description="The URL includes a parameter commonly used to redirect users to another site.",
                evidence={"parameters": sorted(redirect_keys.intersection(query.keys()))}, score=15,
            ))

        # Optional external reputation checks. These are skipped by default in development.
        if self.config.external_checks_enabled:
            for external_finding in self._external_checks(url):
                findings.append(external_finding)

        if not findings:
            findings.append(Finding(
                type="no_obvious_url_risk", severity="info", title="No obvious URL risk found",
                description="No local heuristic warning was triggered. This does not guarantee the URL is safe.",
                evidence={"sha256": hashlib.sha256(url.encode()).hexdigest()}, score=0,
            ))

        return [finding.to_dict() for finding in findings]

    def _external_checks(self, url: str) -> List[Finding]:
        findings: List[Finding] = []
        for service_name, service in [
            ("Google Safe Browsing", self.google_safe_browsing),
            ("VirusTotal", self.virustotal),
            ("urlscan.io", self.urlscan),
        ]:
            result = service.check_url(url)
            if result.get("skipped"):
                continue
            if result.get("error"):
                findings.append(Finding(
                    type="external_check_error", severity="info", title=f"{service_name} check unavailable",
                    description="The external reputation service could not be reached or returned an error.",
                    evidence={"service": service_name, "error": result.get("error")}, score=0,
                ))
            elif result.get("malicious") or result.get("suspicious"):
                findings.append(Finding(
                    type="external_reputation", severity="critical" if result.get("malicious") else "high",
                    title=f"{service_name} flagged this URL",
                    description="An external reputation provider reported suspicious or malicious indicators.",
                    evidence={"service": service_name, "summary": result.get("summary", {})}, score=45 if result.get("malicious") else 30,
                ))
        return findings

    def _is_ip_host(self, hostname: str) -> bool:
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            return False

    def _is_private_or_local_ip(self, hostname: str) -> bool:
        try:
            ip = ipaddress.ip_address(hostname)
            return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast
        except ValueError:
            return False

    def _entropy(self, value: str) -> float:
        if not value:
            return 0.0
        probabilities = [value.count(char) / len(value) for char in set(value)]
        return -sum(p * math.log2(p) for p in probabilities)

    def _safe_preview(self, value: str) -> str:
        return value[:180] + ("..." if len(value) > 180 else "")
