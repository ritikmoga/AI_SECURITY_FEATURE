from pathlib import Path

from src.config import AppConfig
from src.detection.device_scanner import DeviceScanner


def test_device_scan_reads_selected_directory_without_execution(tmp_path: Path):
    (tmp_path / "safe.txt").write_text("harmless project test", encoding="utf-8")
    report = DeviceScanner(AppConfig(max_file_size_mb=1)).scan_directory(tmp_path)
    assert report["metadata"]["files_scanned"] == 1
    assert report["metadata"]["static_analysis_only"] is True
