# Backend OpenTelemetry Tracing

- commit title: backend opentelemetry tracing
- changed file scope: `src/backend/app/core/tracing.py`, `src/backend/app/core/database.py`, `src/backend/app/main.py`, `src/backend/app/core/settings.py`, backend dependency files, backend docs, localized backend docs, tracing tests
- reason: add an optional vendor-neutral tracing layer after request correlation, metrics, and health checks
- impact: when `TRACING_ENABLED=true`, FastAPI, SQLAlchemy, and Redis can emit OTLP traces with service/environment metadata; tracing remains disabled by default to avoid local collector requirements
