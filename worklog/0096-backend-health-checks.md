# Backend Health Checks

- commit title: backend health checks
- changed file scope: `src/backend/app/core/health.py`, `src/backend/app/main.py`, backend docs, localized backend docs, health tests
- reason: add operational liveness and readiness endpoints for deployment probes and monitoring
- impact: `/health/live` returns process liveness and `/health/ready` verifies database and Redis availability, returning 503 when dependencies are degraded
