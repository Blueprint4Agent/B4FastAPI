# Commit Title

feat(env): add environment sync and consistency checks

# Changed File Scope

- scripts/env.py and Makefile
- docker/scripts/docker-deploy.sh
- .github/workflows/build.yml
- .gitignore and .dockerignore
- README.md and notes/ko/README.md
- worklog/0137-env-sync-harness.md

# Reason

Existing initialization only copied missing files. Template additions and layout
changes did not reach existing env files, and shared development/deployment keys
could drift without CI detecting them.

# Impact

Separate development and Docker sync/check commands. Sync follows example comments,
blank lines, and key ordering while retaining literal existing values and preserving
additional keys in a trailing section. Timestamped owner-only backups precede changes
and are excluded from Git and Docker contexts. Shared example key checks run through
make check/ci and GitHub backend checks; deployment checks docker/.env before build.
Deployment now requires uv. This validates keys/layout, not credentials or live state.
Actual local env files were not modified. No new persistent test harness was added.

# Loop Alignment

Backend request lifecycle, domain events, background tasks, and frontend API state,
realtime refresh, desktop recovery, and UI composition loops are not applicable:
changes affect environment tooling and CI only.

# Verification

- make help confirmed the new commands.
- make check and make test passed with temporary SQLite, in-memory Redis, metrics
  enabled, and email/OAuth/tracing disabled: 70 backend and 51 frontend tests passed;
  3 existing backend dependency deprecation warnings.
- Root script has no existing Make lint/format target; applied backend Ruff config
  directly to scripts/env.py, then reran make env-contract-check successfully.
- Temporary fixtures exercised the real Make targets: layout/inline comments,
  quoted and empty value preservation, extra keys, backup contents/mode, idempotence,
  scope isolation, shared-key drift failure, and duplicate-key rejection all passed.
- git diff --check passed.
