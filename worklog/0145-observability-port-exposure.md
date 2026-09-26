# Commit Title

fix(observability): keep Tempo and Loki ports internal

# Changed File Scope

- docker/docker-compose.yml and docker/.env.example
- scripts/env.py
- README.md and notes/ko/README.md
- worklog/0145-observability-port-exposure.md

# Reason

Expose Grafana, Prometheus and the OTLP receiver on the development host while
keeping Tempo and Loki accessible through the Compose network only.

# Impact

Remove Tempo's host port mapping and the obsolete TEMPO_HOST_PORT template key
and environment-contract exception. Loki already has no published port.
Document internal Grafana/Collector endpoints and removal of the unused local
env key. Preserve data volumes and existing internal service ports.

# Loop Alignment

Backend request lifecycle, domain events, background tasks and frontend API,
realtime, desktop recovery and UI composition loops are not applicable: this
change only affects infrastructure port exposure and documentation.

# Verification

- make check, Compose config --quiet and git diff --check passed.
- In the preceding live operation, recreated Tempo and confirmed both Tempo and
  Loki have empty HostConfig.PortBindings and are running; data volumes preserved.
- Prometheus had a configured host binding but an empty runtime mapping. Recreating
  only Prometheus restored 127.0.0.1:9090 and its /-/ready endpoint returned ready.
  This was a runtime repair, not a Prometheus source configuration change; the
  original cause of the missing mapping was not established.
- Local tests skipped following the preceding user instruction; CI remains enabled.
