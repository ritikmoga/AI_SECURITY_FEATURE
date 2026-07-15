"""Configuration checks for read-only serverless deployment filesystems."""
from src.config import AppConfig


def test_vercel_uses_writable_tmp_paths(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.delenv("REPORT_STORAGE_PATH", raising=False)

    config = AppConfig.from_env()

    assert config.database_path.as_posix() == "/tmp/scamshield.db"
    assert config.report_storage_path.as_posix() == "/tmp/reports.json"
