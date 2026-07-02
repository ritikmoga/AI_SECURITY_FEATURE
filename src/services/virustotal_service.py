"""VirusTotal optional URL reputation client."""
from __future__ import annotations

import base64
from typing import Any, Dict

import requests

from src.config import AppConfig


class VirusTotalService:
    ENDPOINT = "https://www.virustotal.com/api/v3/urls"

    def __init__(self, config: AppConfig):
        self.config = config

    def check_url(self, url: str) -> Dict[str, Any]:
        if not (self.config.external_checks_enabled and self.config.virustotal_api_key):
            return {"skipped": True, "reason": "VirusTotal API key not configured."}
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        try:
            response = requests.get(
                f"{self.ENDPOINT}/{url_id}",
                headers={"x-apikey": self.config.virustotal_api_key},
                timeout=8,
            )
            if response.status_code == 404:
                return {"suspicious": False, "summary": {"message": "URL not found in VirusTotal cache."}}
            response.raise_for_status()
            data = response.json().get("data", {}).get("attributes", {})
            stats = data.get("last_analysis_stats", {})
            malicious = int(stats.get("malicious", 0) or 0)
            suspicious = int(stats.get("suspicious", 0) or 0)
            return {
                "malicious": malicious > 0,
                "suspicious": suspicious > 0,
                "summary": {"analysis_stats": stats},
            }
        except requests.RequestException as exc:
            return {"error": str(exc)}
