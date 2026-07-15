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
    database_path: Path = Path("./data/scamshield.db")
    auth_secret_key: str = "change-this-in-production"
    google_oauth_client_id: str = ""
    database_url: str = ""
    redis_url: str = ""
    jwt_access_token_minutes: int = 20
    jwt_refresh_token_days: int = 14
    admin_emails: set[str] = field(default_factory=set)

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

        # Vercel functions can write only to /tmp.  Keep the local defaults for
        # desktop development, but use an ephemeral safe location in serverless
        # deployments until a hosted PostgreSQL DATABASE_URL is configured.
        serverless_tmp = Path("/tmp") if os.getenv("VERCEL") else Path("./data")
        report_storage_path = Path(os.getenv("REPORT_STORAGE_PATH", str(serverless_tmp / "reports.json")))
        database_path = Path(os.getenv("DATABASE_PATH", str(serverless_tmp / "scamshield.db")))

        return cls(
            version=os.getenv("SCAMSHIELD_VERSION", "1.0.0"),
            cors_origins=os.getenv("CORS_ORIGINS", "*"),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "10")),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            report_storage_path=report_storage_path,
            external_checks_enabled=os.getenv("EXTERNAL_CHECKS_ENABLED", "false").lower() == "true",
            allowed_extensions=parsed_extensions,
            google_safe_browsing_api_key=os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", ""),
            virustotal_api_key=os.getenv("VIRUSTOTAL_API_KEY", ""),
            urlscan_api_key=os.getenv("URLSCAN_API_KEY", ""),
            database_path=database_path,
            auth_secret_key=os.getenv("AUTH_SECRET_KEY", "change-this-in-production"),
            google_oauth_client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            redis_url=os.getenv("REDIS_URL", ""),
            jwt_access_token_minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "20")),
            jwt_refresh_token_days=int(os.getenv("JWT_REFRESH_TOKEN_DAYS", "14")),
            admin_emails={item.strip().lower() for item in os.getenv("ADMIN_EMAILS", "").split(",") if item.strip()},
        )
