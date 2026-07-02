"""urlscan.io optional lookup client.

This uses lookup/search only in the current implementation. Automatic submission of
user URLs should be a deliberate product decision because submitted URLs may become
visible to third-party services depending on account settings.
"""
from __future__ import annotations

from typing import Any, Dict

import requests

from src.config import AppConfig


class UrlscanService:
    SEARCH_ENDPOINT = "https://urlscan.io/api/v1/search/"

    def __init__(self, config: AppConfig):
        self.config = config

    def check_url(self, url: str) -> Dict[str, Any]:
        if not (self.config.external_checks_enabled and self.config.urlscan_api_key):
            return {"skipped": True, "reason": "urlscan.io API key not configured."}
        try:
            response = requests.get(
                self.SEARCH_ENDPOINT,
                params={"q": f'page.url:"{url}"'},
                headers={"API-Key": self.config.urlscan_api_key},
                timeout=8,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            verdicts = [item.get("verdicts", {}).get("overall", {}) for item in results[:5]]
            malicious = any(v.get("malicious") for v in verdicts)
            suspicious = any(v.get("score", 0) >= 50 for v in verdicts)
            return {"malicious": malicious, "suspicious": suspicious, "summary": {"result_count": len(results)}}
        except requests.RequestException as exc:
            return {"error": str(exc)}
