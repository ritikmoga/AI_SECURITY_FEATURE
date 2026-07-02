"""Application configuration."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_ALLOWED_EXTENSIONS = {
    ".txt", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".doc", ".docx", ".docm", ".xls", ".xlsx", ".xlsm", ".ppt", ".pptx", ".pptm",
    ".zip", ".csv", ".json", ".eml"
}


@dataclass(frozen=True)
class AppConfig:
    """Central app settings loaded from environment variables."""

    version: str = "1.0.0"
    cors_origins: str = "*"
    max_file_size_mb: int = 10
    rate_limit_per_minute: int = 60
    report_storage_path: Path = Path("./data/reports.json")
    external_checks_enabled: bool = False
    allowed_extensions: set[str] = field(default_factory=lambda: set(DEFAULT_ALLOWED_EXTENSIONS))
    google_safe_browsing_api_key: str = ""
    virustotal_api_key: str = ""
    urlscan_api_key: str = ""

    @classmethod
    def from_env(cls) -> "AppConfig":
        allowed_extensions = os.getenv("ALLOWED_EXTENSIONS")
        parsed_extensions = set(DEFAULT_ALLOWED_EXTENSIONS)
        if allowed_extensions:
            parsed_extensions = {
                ext.strip().lower() if ext.strip().startswith(".") else f".{ext.strip().lower()}"
                for ext in allowed_extensions.split(",")
                if ext.strip()
            }

        return cls(
            version=os.getenv("SCAMSHIELD_VERSION", "1.0.0"),
            cors_origins=os.getenv("CORS_ORIGINS", "*"),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "10")),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            report_storage_path=Path(os.getenv("REPORT_STORAGE_PATH", "./data/reports.json")),
            external_checks_enabled=os.getenv("EXTERNAL_CHECKS_ENABLED", "false").lower() == "true",
            allowed_extensions=parsed_extensions,
            google_safe_browsing_api_key=os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", ""),
            virustotal_api_key=os.getenv("VIRUSTOTAL_API_KEY", ""),
            urlscan_api_key=os.getenv("URLSCAN_API_KEY", ""),
        )
