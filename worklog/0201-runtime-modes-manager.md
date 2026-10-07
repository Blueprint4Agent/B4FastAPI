# Commit Title

feat(auth): separate runtime modes and add manager access

# Changed File Scope

Backend runtime mode validation, dedicated bootstrap, manager guards/audit/migration, contracts, grouped environment examples with per-variable value hints, tests/docs and frontend integration.

# Reason

Separate development-only entry points from authenticated production before adding a read-only manager role.

# Design

Phase 1: APP_MODE development/production, production requires login, dedicated bootstrap identity with no email-collision promotion; mode-aware safe home and hidden/blocked developer routes. Phase 2: manager can read directory/statistics only; CLI role assignment retains last-admin protection and records audit events. Adopt coordinated API contract in B4React, merge child before parent pin.

# Verification Plan

Full make verify-plan / make verify, role and mode authorization/DB tests, contract generation, production route and UI checks. Compare shared sidebar/settings/admin family at mobile/desktop in both themes.

# Impact

Existing users retain roles. Development remains the default for existing local environments; deployment example explicitly selects production. Production disables bootstrap identities and requires authentication. No application role mutation API is added.

# Loop Alignment

Keep router/dependency/service/repository ownership; roles are read from DB each request. UI consumes shared config/auth owners, revalidates role data via existing auth lifecycle. No new realtime or background operation is needed; role writes/audit are transactional.

# Verification

Full make verify-plan / make verify selected backend=True and frontend=full: 232 backend tests, frontend 125 tests, 114 browser UI tests, 8 production route tests, 3 Style Studio tests; hooks, architecture, contracts, packaging and project build checks passed. No checks intentionally omitted. Mode-transition tests cover bearer/API keys and bootstrap collisions; manager tests cover grant/revoke, audit and last-admin protection; populated migration roundtrip passes. Environment synchronization preserves all pre-existing values, keeps the effective development mode for existing deployments and passes env-check/docker-env-check/env-contract-check. Full follow-up make verify-plan / make verify passed after adding environment comments; no checks were omitted.

Frontend integration: B4React PR #53 merged with merge commit 78d0e00fb03076adc7fe8072c153e387132f0268 before updating the parent gitlink. Local child push and actual PR governance checks passed. Environment examples document all 84 backend, 96 Docker and 1 frontend managed variables.
