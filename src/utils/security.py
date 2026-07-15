"""HTTP hardening helpers shared by the Flask API."""
from __future__ import annotations

import uuid
from typing import Any


def request_id() -> str:
    """Use a client request ID when valid, otherwise produce a traceable ID."""
    from flask import request

    supplied = request.headers.get("X-Request-ID", "")
    return supplied[:128] if supplied and supplied.replace("-", "").isalnum() else str(uuid.uuid4())


def apply_security_headers(response: Any, trace_id: str) -> Any:
    response.headers["X-Request-ID"] = trace_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store" if "/auth/" in response.headers.get("Content-Location", "") else "private, no-store"
    return response
