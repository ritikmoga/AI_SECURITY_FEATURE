"""Small SQLite persistence layer for users and their scan reports.

The existing PostgreSQL schema remains suitable for production deployments.  This
store provides a secure zero-setup database for the Flask application locally.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class UserStore:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                PRAGMA foreign_keys = ON;
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    google_subject TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    avatar_url TEXT,
                    role TEXT NOT NULL DEFAULT 'user',
                    created_at TEXT NOT NULL,
                    last_login_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS scan_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    scan_id TEXT NOT NULL UNIQUE,
                    scan_type TEXT NOT NULL,
                    target TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_scan_reports_user_created ON scan_reports(user_id, created_at DESC);
            """)
            try:
                conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")
            except sqlite3.OperationalError:
                pass

    def upsert_google_user(self, subject: str, email: str, name: str, picture: str | None, role: str = "user") -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO users (google_subject, email, display_name, avatar_url, role, created_at, last_login_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(google_subject) DO UPDATE SET
                    email=excluded.email, display_name=excluded.display_name,
                    avatar_url=excluded.avatar_url, role=excluded.role, last_login_at=excluded.last_login_at
            """, (subject, email.lower(), name[:120], picture, role, now, now))
            row = conn.execute("SELECT * FROM users WHERE google_subject = ?", (subject,)).fetchone()
        return dict(row)

    def save_report(self, user_id: int, report: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO scan_reports
                (user_id, scan_id, scan_type, target, risk_score, risk_level, report_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, report["scan_id"], report["scan_type"], report["target"],
                  report["risk_score"], report["risk_level"], json.dumps(report), report["created_at"]))

    def list_reports(self, user_id: int, limit: int = 30) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("SELECT report_json FROM scan_reports WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
        return [json.loads(row["report_json"]) for row in rows]

    def dashboard(self, user_id: int) -> dict[str, int]:
        """Return aggregate account statistics without exposing report contents."""
        with self._connect() as conn:
            row = conn.execute("""
                SELECT COUNT(*) AS total, COALESCE(ROUND(AVG(risk_score)), 0) AS average,
                    SUM(CASE WHEN risk_level IN ('High Risk', 'Dangerous') THEN 1 ELSE 0 END) AS high_risk
                FROM scan_reports WHERE user_id = ?
            """, (user_id,)).fetchone()
        return {"total": int(row["total"]), "average": int(row["average"]), "high_risk": int(row["high_risk"] or 0)}

    def delete_report(self, user_id: int, scan_id: str) -> bool:
        """Delete only a report owned by the authenticated user."""
        with self._connect() as conn:
            result = conn.execute("DELETE FROM scan_reports WHERE user_id = ? AND scan_id = ?", (user_id, scan_id))
        return result.rowcount > 0
