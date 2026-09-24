# Commit Title

fix(docker): limit observability shutdown to its services

# Changed File Scope

- Makefile
- README.md
- notes/ko/README.md
- worklog/0136-observability-stop-scope.md

# Reason

The observability shutdown target used Compose down, which also removed the app
and database services in the same project.

# Impact

Stop only Grafana, Prometheus, OpenTelemetry Collector, and Tempo. Preserve the
app, PostgreSQL, Redis, stopped containers, and data volumes. Document restart
behavior in English and Korean. Container names are unchanged.

# Loop Alignment

Backend request lifecycle, domain events, and background tasks and frontend API
state, realtime refresh, desktop recovery, and UI composition loops are not
applicable: this change only scopes a Docker Make target and its documentation.

# Verification

- make help and make -n docker-observability-down confirm the target and four-service stop command.
- git diff --check passed.
- Initial make check passed; make test had 7 backend failures because local PostgreSQL authentication failed (63 passed).
- Repeat make check and make test with temporary SQLite, in-memory Redis, metrics enabled, and email/OAuth/tracing disabled; results recorded below.
- No running containers were stopped for this validation.
- Repeat succeeded: make check passed; backend 70 tests and frontend 51 tests passed. Backend emitted 3 existing dependency deprecation warnings.
