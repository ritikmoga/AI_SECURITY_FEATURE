# Database

`users_schema.sql` is the PostgreSQL 13+ production schema for accounts,
sessions, preferences, scan reports, and audit events. The Flask development
server uses SQLite at `data/scamshield.db` so it runs without external services.

Before switching production code to PostgreSQL, apply the schema using:

```bash
psql "$DATABASE_URL" -f database/users_schema.sql
psql "$DATABASE_URL" -f database/migrations/001_google_auth.sql
```
