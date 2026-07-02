from src.config import AppConfig
from src.detection.url_checker import URLChecker


def test_url_checker_safe_example_has_info_finding():
    checker = URLChecker(AppConfig())
    findings = checker.analyze_url("https://example.com")
    assert any(f["type"] == "no_obvious_url_risk" for f in findings)


def test_url_checker_flags_http_ip_url():
    checker = URLChecker(AppConfig())
    findings = checker.analyze_url("http://192.168.1.10/login")
    types = {f["type"] for f in findings}
    assert "ip_based_url" in types
    assert "local_network_url" in types


def test_url_checker_extracts_urls():
    checker = URLChecker(AppConfig())
    urls = checker.extract_urls("Open https://example.com and http://example.org/test.")
    assert "https://example.com" in urls
    assert "http://example.org/test" in urls
