"""Capture real local ScamShield UI results for the project presentation."""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "live-screenshots"
URL = "http://127.0.0.1:5174"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def shot(page, name: str) -> None:
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)


def result_shot(page, name: str) -> None:
    page.locator(".result-panel").screenshot(path=str(OUT / f"{name}_detail.png"))


def scan_url(page, url: str, output: str) -> str:
    page.get_by_role("button", name="URL scanner").click()
    page.get_by_label("URL to scan").fill(url)
    page.get_by_role("button", name="Scan URL").click()
    page.get_by_role("heading", name="Recent scans").wait_for()
    page.wait_for_timeout(600)
    shot(page, output)
    result_shot(page, output)
    history = json.loads(page.evaluate("localStorage.getItem('scamshield.scan.history.v1')"))
    return history[0]["scan_id"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=CHROME, headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
        page.goto(URL, wait_until="networkidle")
        shot(page, "01_dashboard")
        report_id = scan_url(page, "https://example.com", "02_url_safe_result")
        scan_url(page, "http://paypal-security-check.example.invalid/login?verify=account", "03_url_high_risk_result")
        page.get_by_role("button", name="Message scanner").click()
        page.get_by_label("Subject").fill("Immediate account review")
        page.get_by_label("Message body").fill("Urgent: verify your account at http://paypal-security-check.example.invalid/login before access is restricted.")
        page.get_by_label("Attachment filenames, optional").fill("invoice.pdf.exe")
        page.get_by_role("button", name="Scan Message").click()
        page.get_by_role("heading", name="Recent scans").wait_for(); page.wait_for_timeout(600); shot(page, "04_message_result"); result_shot(page, "04_message_result")
        page.get_by_role("button", name="File scanner").click()
        page.locator('input[type="file"]').set_input_files(str(ROOT / "tests" / "fixtures" / "safe_test.txt"))
        page.get_by_role("button", name="Scan File").click()
        page.get_by_role("heading", name="Recent scans").wait_for(); page.wait_for_timeout(600); shot(page, "05_file_result"); result_shot(page, "05_file_result")
        page.get_by_role("button", name="QR scanner").click()
        page.get_by_label("QR decoded text or URL").fill("https://example.com")
        page.get_by_role("button", name="Scan QR Text").click()
        page.get_by_role("heading", name="Recent scans").wait_for(); page.wait_for_timeout(600); shot(page, "06_qr_result"); result_shot(page, "06_qr_result")
        page.get_by_role("button", name="Report lookup").click()
        page.get_by_label("Scan report ID").fill(report_id)
        page.get_by_role("button", name="Fetch Report").click()
        page.get_by_role("heading", name="Recent scans").wait_for(); page.wait_for_timeout(600); shot(page, "07_report_lookup_result"); result_shot(page, "07_report_lookup_result")
        browser.close()


if __name__ == "__main__":
    main()
