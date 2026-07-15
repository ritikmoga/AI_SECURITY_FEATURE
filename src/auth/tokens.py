"""Short-lived JWT access and refresh token support."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt


class TokenManager:
    def __init__(self, secret: str, access_minutes: int, refresh_days: int) -> None:
        self.secret = secret
        self.access_minutes = access_minutes
        self.refresh_days = refresh_days

    def issue_pair(self, user: dict[str, Any]) -> dict[str, str]:
        return {
            "access_token": self._encode(user, "access", timedelta(minutes=self.access_minutes)),
            "refresh_token": self._encode(user, "refresh", timedelta(days=self.refresh_days)),
        }

    def read(self, token: str, expected_type: str = "access") -> dict[str, Any] | None:
        try:
            payload = jwt.decode(token, self.secret, algorithms=["HS256"], options={"require": ["exp", "iat", "sub", "type"]})
            return payload if payload.get("type") == expected_type else None
        except jwt.PyJWTError:
            return None

    def _encode(self, user: dict[str, Any], token_type: str, lifetime: timedelta) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode({"sub": str(user["id"]), "email": user["email"], "name": user["display_name"],
                           "role": user.get("role", "user"), "type": token_type, "iat": now, "exp": now + lifetime},
                          self.secret, algorithm="HS256")
