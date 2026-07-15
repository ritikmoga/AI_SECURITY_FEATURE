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
from src.auth.tokens import TokenManager
from src.detection.malware_detector import MalwareDetector
from src.detection.qr_checker import QRChecker
from src.detection.url_checker import URLChecker
from src.scoring.risk_score import RiskScorer
from src.storage.report_store import ReportStore
from src.storage.user_store import UserStore
from src.storage.postgres_user_store import PostgresUserStore
from src.utils.rate_limit import InMemoryRateLimiter
from src.utils.redis_rate_limit import RedisRateLimiter
from src.utils.security import apply_security_headers, request_id
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
    users = PostgresUserStore(app_config.database_url) if app_config.database_url else UserStore(app_config.database_path)
    limiter = (RedisRateLimiter(app_config.redis_url, app_config.rate_limit_per_minute, 60)
               if app_config.redis_url else InMemoryRateLimiter(app_config.rate_limit_per_minute, 60))
    tokens = TokenManager(app_config.auth_secret_key, app_config.jwt_access_token_minutes, app_config.jwt_refresh_token_days)

    def client_key() -> str:
        forwarded = request.headers.get("X-Forwarded-For", "")
        return (forwarded.split(",")[0].strip() or request.remote_addr or "unknown")

    @app.before_request
    def _assign_request_id() -> None:
        request.environ["scamshield.request_id"] = request_id()

    @app.after_request
    def _security_headers(response: Any) -> Any:
        return apply_security_headers(response, request.environ.get("scamshield.request_id", "unknown"))

    def current_user() -> Dict[str, Any] | None:
        """Return the signed session payload, or None for anonymous scanners."""
        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return None
        try:
            payload = tokens.read(authorization[7:])
            if not payload:
                return None
            return {"id": payload["sub"], "email": payload["email"], "display_name": payload["name"], "role": payload["role"]}
        except (KeyError, TypeError, ValueError):
            return None

    def save_for_signed_in_user(report: Dict[str, Any]) -> None:
        user = current_user()
        if user:
            users.save_report(user["id"], report)

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
            "google_sign_in_enabled": bool(app_config.google_oauth_client_id),
        })

    @app.post("/api/auth/google")
    def google_sign_in() -> Any:
        """Verify a Google ID token server-side and issue a short-lived app session."""
        if not app_config.google_oauth_client_id:
            return jsonify({"status": "error", "message": "Google sign-in is not configured."}), 503
        try:
            credential = require_json(request).get("credential")
            credential = ensure_text(credential, field="credential", max_length=12000)
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token
            claims = id_token.verify_oauth2_token(credential, google_requests.Request(), app_config.google_oauth_client_id)
            if not claims.get("email_verified") or not claims.get("sub") or not claims.get("email"):
                raise ValidationError("Google could not verify this email address.")
            email = str(claims["email"]).lower()
            user = users.upsert_google_user(
                str(claims["sub"]), email, str(claims.get("name") or email), claims.get("picture"),
                role="admin" if email in app_config.admin_emails else "user",
            )
            public_user = {key: user[key] for key in ("id", "email", "display_name", "avatar_url", "role")}
            token_pair = tokens.issue_pair(public_user)
            return jsonify({"status": "success", "data": {"token": token_pair["access_token"], "refresh_token": token_pair["refresh_token"], "user": public_user}})
        except ValidationError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400
        except ValueError:
            return jsonify({"status": "error", "message": "The Google credential was invalid or expired."}), 401
        except Exception:
            app.logger.exception("Google sign-in failed")
            return jsonify({"status": "error", "message": "Google sign-in could not be completed."}), 500

    @app.post("/api/auth/refresh")
    def refresh_session() -> Any:
        try:
            refresh_token = ensure_text(require_json(request).get("refresh_token"), field="refresh_token", max_length=4096)
            payload = tokens.read(refresh_token, expected_type="refresh")
            if not payload:
                return jsonify({"status": "error", "message": "Refresh token is invalid or expired."}), 401
            user = {"id": payload["sub"], "email": payload["email"], "display_name": payload["name"], "role": payload["role"]}
            pair = tokens.issue_pair(user)
            return jsonify({"status": "success", "data": {"token": pair["access_token"], "refresh_token": pair["refresh_token"], "user": user}})
        except ValidationError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400

    @app.get("/api/auth/me")
    def auth_me() -> Any:
        user = current_user()
        if not user:
            return jsonify({"status": "error", "message": "Sign in is required."}), 401
        return jsonify({"status": "success", "data": user})

    @app.get("/api/user/reports")
    def user_reports() -> Any:
        user = current_user()
        if not user:
            return jsonify({"status": "error", "message": "Sign in is required."}), 401
        limit = min(max(request.args.get("limit", 30, type=int), 1), 100)
        return jsonify({"status": "success", "data": users.list_reports(user["id"], limit)})

    @app.get("/api/user/dashboard")
    def user_dashboard() -> Any:
        user = current_user()
        if not user:
            return jsonify({"status": "error", "message": "Sign in is required."}), 401
        return jsonify({"status": "success", "data": users.dashboard(user["id"])})

    @app.get("/api/admin/overview")
    def admin_overview() -> Any:
        user = current_user()
        if not user or user.get("role") != "admin":
            return jsonify({"status": "error", "message": "Administrator access is required."}), 403
        return jsonify({"status": "success", "data": {"service": "scamshield-ai", "storage": "postgresql" if app_config.database_url else "sqlite", "rate_limiter": "redis" if app_config.redis_url else "memory", "external_checks_enabled": app_config.external_checks_enabled}})

    @app.post("/api/scan/url")
    def scan_url() -> Any:
        try:
            data = require_json(request)
            url = validate_url_input(data.get("url"))
            findings = url_checker.analyze_url(url)
            report = scorer.build_report(scan_type="url", target=url, findings=findings)
            stored = reports.save(report)
            save_for_signed_in_user(stored)
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
            save_for_signed_in_user(stored)
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
            save_for_signed_in_user(stored)
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
            save_for_signed_in_user(stored)
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
