# KoKoroMichi SaaS Deployment Guide

## Quick Start (Local Dev)

1. Copy `.env.example` to `.env` and fill in secrets.
2. Run with Docker Compose:

```bash
docker-compose up --build
```

## Health & Metrics Endpoints

- `/healthz` — liveness probe (returns 200 OK if running)
- `/readyz` — readiness probe (checks DB/Redis connectivity)
- `/metrics` — Prometheus format metrics (requests, purchases, queue length, etc.)

## Environment Variables

See `env.example` for all supported variables.

## CI/CD

- CI: `.github/workflows/ci.yml` — runs lint, tests on every push/PR
- CD: `.github/workflows/cd.yml` — builds/pushes Docker image, triggers deploy hook

## Worker Queue

- Celery worker defined in `services/worker.py`
- Enqueue tasks from bot code:

```python
from services.worker import run_arena_match
run_arena_match.delay('match123', 'guild456')
```

## Multi-Tenant & Fallback

- `SINGLE_TENANT_MODE=true` — local JSON only
- `SINGLE_TENANT_MODE=false` — SaaS mode (DB, Redis)
- `AUTO_FALLBACK=true` — auto-switch to local mode if provider fails

## Deployment Targets

- Local: Docker Compose
- Cloud: Render, Railway, AWS ECS, GKE, or any Docker-compatible host

## Security & Observability

- Structured logging (JSON)
- Sentry integration (set `SENTRY_DSN`)
- Metrics endpoint for Prometheus
- Secrets via env vars or Vault

## Backups & Migrations

- Schedule DB backups to S3
- Use Alembic for schema migrations
- On startup, check DB/Redis health and run migrations if needed

---

For more, see full migration plan in `STORE_SYSTEM_COMPLETE.md`.
