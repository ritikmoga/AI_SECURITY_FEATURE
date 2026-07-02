"""ScamShield AI - defensive security scanning API.

Run locally:
    python app.py

This app performs safe, non-executing analysis of URLs, messages, files, and QR text.
External reputation checks are optional and only run when API keys are configured.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.config import AppConfig
from src.detection.malware_detector import MalwareDetector
from src.detection.qr_checker import QRChecker
from src.detection.url_checker import URLChecker
from src.scoring.risk_score import RiskScorer
from src.storage.report_store import ReportStore
from src.utils.rate_limit import InMemoryRateLimiter
from src.utils.validation import ValidationError, ensure_text, require_json, validate_url_input

load_dotenv()


def create_app(config: AppConfig | None = None) -> Flask:
    app = Flask(__name__)
    app_config = config or AppConfig.from_env()
    app.config["MAX_CONTENT_LENGTH"] = app_config.max_file_size_mb * 1024 * 1024
    CORS(app, resources={r"/api/*": {"origins": app_config.cors_origins}})

    url_checker = URLChecker(app_config)
    malware_detector = MalwareDetector(app_config)
    qr_checker = QRChecker(app_config, url_checker=url_checker)
    scorer = RiskScorer()
    reports = ReportStore(app_config.report_storage_path)
    limiter = InMemoryRateLimiter(max_requests=app_config.rate_limit_per_minute, window_seconds=60)

    def client_key() -> str:
        forwarded = request.headers.get("X-Forwarded-For", "")
        return (forwarded.split(",")[0].strip() or request.remote_addr or "unknown")

    @app.before_request
    def _rate_limit() -> Any:
        if request.path.startswith("/api/"):
            allowed, retry_after = limiter.allow(client_key())
            if not allowed:
                return jsonify({
                    "status": "error",
                    "error": "rate_limited",
                    "message": "Too many requests. Please try again later.",
                    "retry_after_seconds": retry_after,
                }), 429
        return None

    @app.get("/")
    def index() -> Any:
        return jsonify({
            "name": "ScamShield AI Security Feature",
            "status": "online",
            "version": app_config.version,
            "docs": "/api/health",
            "endpoints": [
                "POST /api/scan/url",
                "POST /api/scan/message",
                "POST /api/scan/file",
                "POST /api/scan/qr",
                "GET /api/scan/report/<scan_id>",
            ],
        })

    @app.get("/api/health")
    def health() -> Any:
        return jsonify({
            "status": "success",
            "service": "scamshield-ai",
            "version": app_config.version,
            "external_checks_enabled": app_config.external_checks_enabled,
            "max_file_size_mb": app_config.max_file_size_mb,
        })

    @app.post("/api/scan/url")
    def scan_url() -> Any:
        try:
            data = require_json(request)
            url = validate_url_input(data.get("url"))
            findings = url_checker.analyze_url(url)
            report = scorer.build_report(scan_type="url", target=url, findings=findings)
            stored = reports.save(report)
            return jsonify({"status": "success", "data": stored}), 200
        except ValidationError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400
        except Exception:
            app.logger.exception("URL scan failed")
            return jsonify({"status": "error", "message": "URL scan failed safely."}), 500

    @app.post("/api/scan/message")
    def scan_message() -> Any:
        try:
            data = require_json(request)
            subject = ensure_text(data.get("subject", ""), field="subject", max_length=300)
            body = ensure_text(data.get("body", ""), field="body", max_length=15000)
            message = {"subject": subject, "body": body, "attachments": data.get("attachments", [])}
            findings = []
            findings.extend(url_checker.check(message))
            findings.extend(malware_detector.detect_message(message))
            report = scorer.build_report(scan_type="message", target="message", findings=findings)
            stored = reports.save(report)
            return jsonify({"status": "success", "data": stored}), 200
        except ValidationError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400
        except Exception:
            app.logger.exception("Message scan failed")
            return jsonify({"status": "error", "message": "Message scan failed safely."}), 500

    @app.post("/api/scan/qr")
    def scan_qr() -> Any:
        try:
            # Safer MVP: accept decoded QR text. Frontend/mobile can decode image client-side.
            data = require_json(request)
            qr_text = ensure_text(data.get("text", ""), field="text", max_length=4096)
            findings = qr_checker.analyze_text(qr_text)
            report = scorer.build_report(scan_type="qr", target="qr_text", findings=findings, metadata={"decoded_text_preview": qr_text[:120]})
            stored = reports.save(report)
            return jsonify({"status": "success", "data": stored}), 200
        except ValidationError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400
        except Exception:
            app.logger.exception("QR scan failed")
            return jsonify({"status": "error", "message": "QR scan failed safely."}), 500

    @app.post("/api/scan/file")
    def scan_file() -> Any:
        if "file" not in request.files:
            return jsonify({"status": "error", "message": "Upload a file using multipart/form-data field named 'file'."}), 400

        uploaded = request.files["file"]
        if not uploaded.filename:
            return jsonify({"status": "error", "message": "Uploaded file has no filename."}), 400

        filename = secure_filename(uploaded.filename)
        suffix = Path(filename).suffix.lower()
        if suffix not in app_config.allowed_extensions:
            return jsonify({
                "status": "error",
                "message": "File type not allowed for this scanner.",
                "allowed_extensions": sorted(app_config.allowed_extensions),
            }), 400

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                uploaded.save(tmp.name)
                temp_path = Path(tmp.name)

            findings, file_meta = malware_detector.analyze_file(temp_path, original_filename=filename)
            report = scorer.build_report(scan_type="file", target=filename, findings=findings, metadata=file_meta)
            stored = reports.save(report)
            return jsonify({"status": "success", "data": stored}), 200
        except Exception:
            app.logger.exception("File scan failed")
            return jsonify({"status": "error", "message": "File scan failed safely."}), 500
        finally:
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    app.logger.warning("Could not delete temporary upload: %s", temp_path)

    @app.get("/api/scan/report/<scan_id>")
    def get_report(scan_id: str) -> Any:
        report = reports.get(scan_id)
        if not report:
            return jsonify({"status": "error", "message": "Report not found."}), 404
        return jsonify({"status": "success", "data": report}), 200

    @app.errorhandler(413)
    def too_large(_: Exception) -> Any:
        return jsonify({"status": "error", "message": f"File is too large. Max size is {app_config.max_file_size_mb} MB."}), 413

    @app.errorhandler(404)
    def not_found(_: Exception) -> Any:
        return jsonify({"status": "error", "message": "Endpoint not found."}), 404

    @app.errorhandler(500)
    def server_error(_: Exception) -> Any:
        return jsonify({"status": "error", "message": "Internal server error."}), 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print("Starting ScamShield AI Security Feature API...")
    print(f"Health check: http://localhost:{port}/api/health")
    app.run(host="0.0.0.0", port=port, debug=debug)
