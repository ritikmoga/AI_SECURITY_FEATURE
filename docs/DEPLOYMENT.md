# Deployment guide

## Containers

Copy `.env.example` to `.env`, set a long `AUTH_SECRET_KEY`, then run:

```bash
docker compose up --build
```

Mount persistent storage for `data/`, terminate TLS at a reverse proxy, restrict
`CORS_ORIGINS` to the frontend domain, and use a managed database before a
public launch.

Set `DATABASE_URL` to enable PostgreSQL account/report persistence and
`REDIS_URL` to enable the Redis distributed rate limiter. Without them, the app
uses local SQLite and an in-memory limiter for development.

## Required production controls

- Set `FLASK_DEBUG=false`.
- Use HTTPS and secure secret management.
- Configure rate limiting with Redis for multiple API instances.
- Send logs and alerts to an approved monitoring system.
- Apply retention and deletion rules to scan reports.
