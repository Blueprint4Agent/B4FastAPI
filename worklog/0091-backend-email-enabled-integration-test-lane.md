# commit title
backend: add email-enabled integration test lane and sync test docs (en/ko)

# changed file scope
- src/backend/tests/conftest.py
- src/backend/tests/integration/api/v1/auth/test_auth_integration.py
- src/backend/pyproject.toml
- src/backend/TEST.md
- docs/ko/backend/TEST.md

# reason
- Integration tests were implicitly sensitive to runtime `EMAIL_ENABLED` values, causing non-deterministic failures in signup/login scenarios.
- Dedicated coverage for `EMAIL_ENABLED=true` behavior (verification required, password-reset branch) was missing.
- Test guide needed explicit marker/fixture/runbook updates in both English and Korean docs.

# impact
- Default `integration_client` now forces deterministic auth baseline with `EMAIL_ENABLED=false`.
- New `email_enabled_integration_client` fixture provides isolated `EMAIL_ENABLED=true` validation lane without external SMTP dependency.
- Added `email_enabled` integration tests for auth verification-required and reset-token consumption flows.
- Registered `email_enabled` pytest marker and documented execution/data-lifecycle rules in `TEST.md` and `docs/ko/backend/TEST.md`.
