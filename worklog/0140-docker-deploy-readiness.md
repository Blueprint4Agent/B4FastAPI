# Commit Title

fix(docker): preserve infrastructure and wait for app readiness

# Changed File Scope

- docker/scripts/docker-up.sh and docker/scripts/docker-export.sh
- docker/docker-compose.yml and Makefile
- README.md and notes/ko/README.md
- worklog/0140-docker-deploy-readiness.md

# Reason

Shell env parsing diverged from Compose, deploy forwarded force-recreate to local
infrastructure, and app startup returned before readiness was confirmed.

# Impact

Read resolved Compose app settings for infrastructure selection and image export.
Preserve existing DB/Redis containers with no-recreate; app-only caller flags include
force-recreate. Use Compose wait with a configurable positive timeout (default 120s)
for each stage. App healthcheck calls health/ready to check DB and Redis. Readiness
failure blocks export via the existing fail-fast deployment script. Document uv/Compose
requirements and explicit infrastructure recreation for configuration changes.
Actual env files, running containers, and volumes were not modified.

# Loop Alignment

Backend lifecycle is observed through the existing readiness endpoint. Domain events
and background tasks remain unchanged. Frontend API state, realtime refresh, desktop
recovery, and UI composition loops are not applicable to deployment tooling changes.

# Verification

- make check passed: env contract, backend lint/format, frontend format/type checks,
  OpenAPI baseline, and generated API checks.
- git diff --check passed.
- Local tests remain skipped following the preceding user instruction; no live Docker
  deployment was performed. GitHub CI remains enabled without bypasses.
