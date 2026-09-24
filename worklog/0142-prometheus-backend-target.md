# Commit Title

feat(observability): configure Prometheus backend target

# Changed File Scope

- docker/docker-compose.yml and docker/.env.example
- docker/observability/prometheus.yml and prometheus-start.sh
- scripts/env.py
- README.md and notes/ko/README.md
- worklog/0142-prometheus-backend-target.md

# Reason

A fixed host.docker.internal:8000 target did not support different host development
ports or direct app service access within the Compose network.

# Impact

Add PROMETHEUS_BACKEND_TARGET (host.docker.internal:8000 by default; app:8000 for a
container backend). Render and validate Prometheus config at startup, reject malformed
target syntax, and add host-gateway mapping. Keep the existing job label for dashboard
and history compatibility. Use the existing default Compose network and document how
the requesting container determines localhost. Add the Docker-only env key exception.
Actual env files and running containers remain unchanged.

# Loop Alignment

Backend request lifecycle, domain events, background tasks, and frontend API state,
realtime refresh, desktop recovery, and UI composition loops are not applicable:
only the external metrics collector configuration changes.

# Verification

- make check passed (environment contract, lint/format, TypeScript and API contracts).
- Compose configuration validation with observability profile passed.
- sh -n docker/observability/prometheus-start.sh and git diff --check passed.
- Local tests were not rerun following the preceding test-skip instruction. No live
  Prometheus restart or scrape verification performed. GitHub CI remains enabled.
