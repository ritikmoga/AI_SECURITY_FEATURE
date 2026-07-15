"""PostgreSQL user/report store for production deployments.

Apply database/users_schema.sql and database/migrations/001_google_auth.sql
before setting DATABASE_URL.
"""
from __future__ import annotations

from typing import Any


class PostgresUserStore:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _connect(self):
        import psycopg
        from psycopg.rows import dict_row
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def upsert_google_user(self, subject: str, email: str, name: str, picture: str | None, role: str = "user") -> dict[str, Any]:
        with self._connect() as conn, conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (google_subject, email, display_name, avatar_url, role, password_hash, email_verified)
                VALUES (%s, %s, %s, %s, %s, NULL, TRUE)
                ON CONFLICT (google_subject) DO UPDATE SET
                    email = EXCLUDED.email, display_name = EXCLUDED.display_name, avatar_url = EXCLUDED.avatar_url,
                    role = EXCLUDED.role, last_login_at = NOW()
                RETURNING id::text, email, display_name, avatar_url, role
            """, (subject, email.lower(), name[:120], picture, role))
            return dict(cursor.fetchone())

    def save_report(self, user_id: str, report: dict[str, Any]) -> None:
        from psycopg.types.json import Jsonb
        with self._connect() as conn, conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO user_scan_reports (user_id, scan_id, scan_type, target, risk_score, risk_level, report)
                VALUES (%s::uuid, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (scan_id) DO UPDATE SET report = EXCLUDED.report
            """, (user_id, report["scan_id"], report["scan_type"], report["target"], report["risk_score"], report["risk_level"], Jsonb(report)))

    def list_reports(self, user_id: str, limit: int = 30) -> list[dict[str, Any]]:
        with self._connect() as conn, conn.cursor() as cursor:
            cursor.execute("SELECT report FROM user_scan_reports WHERE user_id = %s::uuid ORDER BY created_at DESC LIMIT %s", (user_id, limit))
            return [row["report"] for row in cursor.fetchall()]

    def dashboard(self, user_id: str) -> dict[str, int]:
        with self._connect() as conn, conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total, COALESCE(ROUND(AVG(risk_score)), 0) AS average,
                COUNT(*) FILTER (WHERE risk_level IN ('High Risk', 'Dangerous')) AS high_risk
                FROM user_scan_reports WHERE user_id = %s::uuid
            """, (user_id,))
            row = cursor.fetchone()
            return {key: int(row[key]) for key in ("total", "average", "high_risk")}
