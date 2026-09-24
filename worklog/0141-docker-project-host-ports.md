# Commit Title

feat(docker): configure project names and published ports

# Changed File Scope

- docker/docker-compose.yml and docker/.env.example
- scripts/env.py
- README.md and notes/ko/README.md
- worklog/0141-docker-project-host-ports.md

# Reason

Fixed container names and published ports prevented concurrent installations and
caused PostgreSQL host-port conflicts with other projects.

# Impact

Let Compose generate container names. Add explicit project-name and host-port
settings for app, PostgreSQL, Redis, Grafana, Prometheus, Tempo, and OTLP. Keep
container ports unchanged and infrastructure host bindings on loopback. Default
project name remains docker to retain current named-volume identity. Extend the
env contract's Docker-only allowlist and explain name/port migration in both locales.
Existing env files, containers, and volumes were not changed.

# Loop Alignment

Backend lifecycle, domain-event, background-task, and frontend API-state, realtime,
desktop recovery, and UI-composition loops are not applicable: this change affects
Compose naming, port publication, and environment tooling only.

# Verification

- make check passed (env contract, lint/format, type and API checks).
- docker compose config --quiet with the observability profile passed.
- git diff --check passed.
- Local tests were not rerun, following the preceding test-skip instruction. This
  change has not been verified by recreating running containers. GitHub CI remains enabled.
