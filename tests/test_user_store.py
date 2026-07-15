from pathlib import Path

from src.storage.user_store import UserStore


def test_google_user_and_report_are_persisted(tmp_path: Path) -> None:
    store = UserStore(tmp_path / "users.db")
    user = store.upsert_google_user("google-subject", "user@example.com", "Test User", None)
    report = {
        "scan_id": "scan-1", "scan_type": "url", "target": "https://example.com",
        "risk_score": 12, "risk_level": "Safe", "created_at": "2026-01-01T00:00:00+00:00",
    }
    store.save_report(user["id"], report)
    assert store.list_reports(user["id"]) == [report]
    assert store.dashboard(user["id"]) == {"total": 1, "average": 12, "high_risk": 0}
