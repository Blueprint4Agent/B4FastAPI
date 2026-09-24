# Commit Title

feat(observability): export application logs to Loki

# Changed File Scope

- src/backend/app/core/observability/log_export.py and logging.py
- src/backend/app/main.py and core/config/settings.py
- src/backend/pyproject.toml and uv.lock
- src/backend/.env.example and docker/.env.example
- docker/docker-compose.yml and docker/observability/{loki,otel-collector}.yml
- docker/observability/grafana/provisioning/datasources/datasources.yml
- Makefile, README.md, notes/ko/README.md, src/backend/BACKEND.md
- worklog/0144-loki-log-pipeline.md

# Reason

Add log storage and Grafana querying alongside existing metrics and traces for
both host-run and containerized backends. Repair the observed Loki startup failure:
the volume root was owned by root while Loki runs as UID 10001.

# Impact

Opt-in LOGS_ENABLED bridges application/Uvicorn logging to the existing OTLP
endpoint using a batch log processor. Preserve console output and structured
request/task correlation. The Collector forwards logs via native OTLP/HTTP to
Loki. Add the Grafana datasource and a persistent Loki volume with seven-day
retention. No Loki host port is published. A one-shot loki-init assigns volume
root ownership to UID/GID 10001 before Loki starts; Loki remains non-root.
Make observability start/stop include Loki. Env templates stay aligned.
Log queues are in memory and do not provide durable audit delivery. Normal process
exit flushes SDK logs; abrupt exit or prolonged outages may lose logs.

# Loop Alignment

Request lifecycle, domain error ownership, domain events, and background task
execution remain unchanged. The existing request/task context is reused by the
new log handler. Frontend loops are not applicable because no frontend code changes.

# Verification

- make check passed; Compose config --quiet and git diff --check passed.
- During the preceding live incident, confirmed root-owned volume and Loki UID
  10001, applied the initialization service, and observed Loki /ready return ready.
- Existing Loki volume data was preserved; only Loki and its initializer were started.
- Local tests were not rerun following the preceding user test-skip instruction.
- End-to-end application log delivery and Grafana querying were not verified live.
