from pathlib import Path

from app import create_app
from src.config import AppConfig


def test_health_endpoint(tmp_path: Path):
    app = create_app(AppConfig(report_storage_path=tmp_path / "reports.json"))
    client = app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "success"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Request-ID"]


def test_scan_url_endpoint(tmp_path: Path):
    app = create_app(AppConfig(report_storage_path=tmp_path / "reports.json"))
    client = app.test_client()
    response = client.post("/api/scan/url", json={"url": "https://example.com"})
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "success"
    assert body["data"]["scan_id"]


def test_scan_message_endpoint(tmp_path: Path):
    app = create_app(AppConfig(report_storage_path=tmp_path / "reports.json"))
    client = app.test_client()
    response = client.post("/api/scan/message", json={"body": "visit https://example.com", "attachments": []})
    assert response.status_code == 200
    assert response.get_json()["data"]["scan_type"] == "message"
