"""Google Safe Browsing optional client."""
from __future__ import annotations

from typing import Any, Dict

import requests

from src.config import AppConfig


class GoogleSafeBrowsingService:
    ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

    def __init__(self, config: AppConfig):
        self.config = config

    def check_url(self, url: str) -> Dict[str, Any]:
        if not (self.config.external_checks_enabled and self.config.google_safe_browsing_api_key):
            return {"skipped": True, "reason": "Google Safe Browsing API key not configured."}
        payload = {
            "client": {"clientId": "scamshield-ai", "clientVersion": self.config.version},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }
        try:
            response = requests.post(
                self.ENDPOINT,
                params={"key": self.config.google_safe_browsing_api_key},
                json=payload,
                timeout=8,
            )
            response.raise_for_status()
            data = response.json()
            matches = data.get("matches", [])
            return {"malicious": bool(matches), "summary": {"matches": matches[:3]}}
        except requests.RequestException as exc:
            return {"error": str(exc)}
