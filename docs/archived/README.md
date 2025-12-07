# KoKoroMichi Discord Bot

## SaaS-Ready Features
- Multi-tenant data isolation (per-guild config, DB schema/tenant_id)
- Automatic fallback to local mode if provider not found
- Containerized (Dockerfile, docker-compose.yml)
- Celery worker for queued jobs
- Structured logging, Sentry, Prometheus metrics
- CI/CD via GitHub Actions

## Quick Start
```bash
cp env.example .env
# Edit .env with your secrets
# Local dev
docker-compose up --build
```

## Health & Metrics
- `/healthz`, `/readyz`, `/metrics` endpoints (see services/health_server.py)

## Worker Queue
- Celery worker: `python -m services.worker`

## CI/CD
- See `.github/workflows/ci.yml` and `cd.yml`

## More
- See `README_SAAS.md` and `STORE_SYSTEM_COMPLETE.md` for full migration plan and architecture.
