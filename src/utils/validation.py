"""Input validation helpers."""
from __future__ import annotations

import re
from urllib.parse import urlparse


class ValidationError(ValueError):
    """Raised when user input is invalid."""


def require_json(request_obj):
    if not request_obj.is_json:
        raise ValidationError("Request body must be JSON.")
    data = request_obj.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request JSON must be an object.")
    return data


def ensure_text(value, *, field: str, max_length: int) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be text.")
    cleaned = value.strip()
    if len(cleaned) > max_length:
        raise ValidationError(f"{field} is too long. Max length is {max_length} characters.")
    return cleaned


def validate_url_input(value) -> str:
    url = ensure_text(value, field="url", max_length=4096)
    if not url:
        raise ValidationError("URL is required.")
    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        raise ValidationError("URL must start with http:// or https://")
    parsed = urlparse(url)
    if not parsed.hostname:
        raise ValidationError("URL must include a valid hostname.")
    return url
