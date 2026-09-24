# Commit Title

fix(docker): align infrastructure credentials and restrict access

# Changed File Scope

- docker/docker-compose.yml and docker/.env.example
- scripts/env.py
- src/backend/app/core/config/settings.py
- src/backend/app/core/db/migrations.py and src/backend/alembic/env.py
- README.md and notes/ko/README.md
- worklog/0138-docker-infra-credentials.md

# Reason

App credentials were configurable while local PostgreSQL and Redis authentication
were not connected to those settings. Infrastructure ports were published on all
interfaces and Grafana allowed anonymous access with default administrator credentials.

# Impact

Align app and local database credentials, enable Redis password authentication when
configured, and use the same password in healthchecks. Bind database and observability
host ports to loopback. Disable Grafana anonymous access and require a non-default
configured administrator password at startup. Allow Docker-only Grafana env keys.
Encode database credentials and Redis passwords in URLs and escape percent signs
for Alembic configuration. Document existing-volume credential rotation requirements.
Existing local env files, containers, and data volumes were not modified.

# Loop Alignment

Backend request, domain event, and background task loops are unchanged; only connection
configuration changes. Frontend API state, realtime refresh, desktop connectivity, and
UI composition loops are not applicable because frontend code is unchanged.

# Verification

- make check passed (env contract, backend lint/format, frontend formatting/typecheck,
  OpenAPI baseline and generated API checks).
- git diff --check passed.
- Local tests and container runtime verification skipped at the user's explicit request.
- Existing GitHub CI remains enabled; no required checks were bypassed.
