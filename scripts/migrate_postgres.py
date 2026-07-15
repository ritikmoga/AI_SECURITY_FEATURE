"""Apply ScamShield's idempotent PostgreSQL schema migrations.

Run locally after loading a DATABASE_URL from Vercel or a managed Postgres
provider. The command deliberately never prints the connection string.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = (
    PROJECT_ROOT / "database" / "users_schema.sql",
    PROJECT_ROOT / "database" / "migrations" / "001_google_auth.sql",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply ScamShield PostgreSQL schema migrations")
    parser.add_argument("--env-file", type=Path, default=PROJECT_ROOT / ".env.local",
                        help="dotenv file containing DATABASE_URL (default: .env.local)")
    parser.add_argument("--verify-only", action="store_true",
                        help="verify core tables without changing the database")
    args = parser.parse_args()
    load_dotenv(args.env_file)
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not database_url:
        parser.error("DATABASE_URL (or POSTGRES_URL) must be set")

    import psycopg

    with psycopg.connect(database_url, autocommit=True) as connection:
        if args.verify_only:
            rows = connection.execute("""
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                  AND tablename IN ('users', 'user_scan_reports', 'user_audit_logs')
                ORDER BY tablename
            """).fetchall()
            print("Verified tables: " + ", ".join(row[0] for row in rows))
            return 0
        for migration in MIGRATIONS:
            connection.execute(migration.read_text(encoding="utf-8"))
            print(f"Applied {migration.relative_to(PROJECT_ROOT)}")
    print("PostgreSQL schema is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
