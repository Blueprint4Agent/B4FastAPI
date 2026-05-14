# Docker Observability Profile

- commit title: docker observability profile
- changed file scope: Docker Compose service profiles and backend observability docs
- reason: keep tracing and metrics services out of the default Docker startup while preserving an explicit way to run the full observability stack
- impact: `docker compose up -d` starts only app, postgres, and redis; `docker compose --profile observability up -d` includes Tempo, OpenTelemetry Collector, Prometheus, and Grafana
