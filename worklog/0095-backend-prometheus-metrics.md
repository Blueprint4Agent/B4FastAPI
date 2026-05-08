# Backend Prometheus Metrics

- commit title: backend prometheus metrics
- changed file scope: `src/backend/app/core/metrics.py`, `src/backend/app/main.py`, `src/backend/app/core/settings.py`, backend dependency files, backend docs, localized backend docs, metrics tests
- reason: add request metrics as the next observability layer after request and trace correlation
- impact: `/metrics` exposes Prometheus-compatible FastAPI request count and latency metrics when `METRICS_ENABLED=true`; the endpoint is excluded from OpenAPI and from self-instrumentation
