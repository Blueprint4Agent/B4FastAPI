# Backend Test Engineering Guide

This document defines backend test architecture and working rules for `src/backend`.
Follow this guide when adding or changing tests.

## 0) Scope and Priority

- Scope: everything under `src/backend/tests`.
- Read order before backend test work:
1. Root `AGENTS.md`
2. `src/backend/BACKEND.md`
3. This document (`src/backend/TEST.md`)
- Priority on conflicts:
1. Root `AGENTS.md`
2. `src/backend/BACKEND.md`
3. This document

## 1) Test Strategy (De Facto, Project-Adapted)

Recommended pyramid:
1. Smoke: app boot and critical route availability
2. API Contract: router-level request/response/auth contract with dependency overrides
3. Unit: service/util logic with mocked dependencies
4. Integration: DB/Redis/external integration with isolated test data
5. E2E: full-system validation in running environment

Current baseline implemented:
1. Smoke test (`tests/test_smoke.py`)
2. API contract tests by domain (`tests/api/v1/<domain>/test_*_api.py`)
3. Integration tests by domain (`tests/integration/api/v1/<domain>/test_*_integration.py`)
4. Full-system seeded integration scenarios (`tests/integration/scenarios/test_full_system_scenario.py`)

## 2) Current Directory Layout

```text
src/backend/tests/
  conftest.py
  test_smoke.py
  api/
    v1/
      auth/
        test_auth_api.py
      api_key/
        test_api_key_api.py
      events/
        test_events_api.py
  integration/
    api/v1/
      auth/
        test_auth_integration.py
      api_key/
        test_api_key_integration.py
    scenarios/
      test_full_system_scenario.py
```

Planned expansion layout:

```text
src/backend/tests/
  unit/
    services/
    utils/
```

## 3) Core Principles

1. Keep `Router -> Service` boundary explicit in tests.
2. Prefer fast, deterministic tests first (smoke + API contract).
3. Use `dependency_overrides` for router tests to replace service/auth dependencies.
4. Avoid real external I/O in smoke/API contract tests.
5. Add integration tests when behavior depends on DB/Redis transaction semantics.

## 4) Smoke Test Rules

- Goal: verify application boot and critical route availability.
- Current endpoint contract: `GET /ping -> 200 {"status":"ok","message":"pong"}`.
- File: `tests/test_smoke.py`.
- Smoke tests must be minimal and always fast.

## 5) API Contract Test Rules (Current Main Harness)

For each API domain:
1. Create `tests/api/v1/<domain>/test_<domain>_api.py`.
2. Build a small test app and include only the target router.
3. Override dependencies (`AuthService`, `APIKeyService`, `get_current_user`, etc.).
4. Assert status code + essential response contract.

Mandatory coverage per domain (minimum):
1. Success case (200/201)
2. Auth failure case (401 when protected)
3. Request validation failure (422) when the endpoint accepts constrained input; do not invent inputs for an input-free GET.

Notes for this codebase:
1. Router tests use fake services, not real repositories.
2. This keeps tests independent from DB and Redis runtime state.
3. API contract tests should use minimal contract payload data, not production-like seed datasets.

## 6) Fixtures and Reuse

- Shared fixtures belong in `tests/conftest.py`.
- Shared API contract payload constants belong in `tests/fixtures/api_contract_data.py`; small domain-local payloads/fixtures may remain beside their tests.
- Shared payload builders (`signup/login`) belong in `tests/fixtures/payload_data.py`.
- Production-like seed dataset constants belong in `tests/fixtures/scenario_seed_data.py`.
- Current shared fixture: `sample_user` (`UserResponse`).
- Keep fixtures small and composable.
- If domain-only fixture is needed, define it near that domain test file.

Seed schema standard (required):
1. Seed user schema: `SeedUserSchema`
   - `email: str`
   - `name: str`
   - `password: str`
   - `role: str`
   - `is_verified: bool`
2. Seed profile schema: `SeedProfileSchema`
   - `profile_name: str`
   - `primary_user: SeedUserSchema`
   - `existing_user_count: int`
   - `existing_user_role: str`
   - `existing_user_email_prefix: str`
   - `existing_user_name_prefix: str`
   - `existing_user_start_index: int`
3. Default profile constant: `DEFAULT_SEED_PROFILE`
4. Seed fixture (`seeded_integration_client`) must consume a `SeedProfileSchema` path, not raw ad-hoc constants.

Scenario flow schema standard (required):
1. Cross-domain scenario input schema belongs in `tests/fixtures/scenario_flow_data.py`.
2. Scenario schema should declare:
   - principal credentials (login email/password)
   - domain-specific action inputs (for example API key name)
   - expected branch flags (for example disabled-key rejection)
3. Scenario tests should consume schema constants (for example `DEFAULT_FULL_SYSTEM_SCENARIO`) instead of inline literals.

## 7) Unit / Integration / E2E Policy

Unit tests:
1. Target service or utility decision logic.
2. Mock repository/external calls.
3. No real DB/network.

Integration tests:
1. Use real test DB/Redis path.
2. Isolate data per test (transaction rollback or dedicated reset fixture).
3. Cover flows where repository/query behavior matters.
4. Include production-like seeded dataset scenarios when business behavior depends on existing records.
5. Use only the seed size required by assertions: a primary-only fixture for one existing principal, default bulk seeds for aggregate/full-system scenarios.
6. Maintain full-system scenario flow under `tests/integration/scenarios/`.
7. Marker boundaries are required:
   - `api_test`: API contract tests only
   - `primary_data`: integration tests on clean primary data state
   - `mocked_data`: integration tests on production-like seeded data
   - `email_enabled`: integration tests that require `EMAIL_ENABLED=true` flow

E2E tests:
1. Run against a real running app instance.
2. Keep only critical user journeys.
3. Do not duplicate broad API contract coverage already done by lower levels.

## 8) Commands

Run all backend tests:

```bash
cd src/backend
TRACING_ENABLED=false uv run pytest
```

Run API contract tests only:

```bash
cd src/backend
TRACING_ENABLED=false uv run pytest -m api_test
```

Run integration tests with clean primary data:

```bash
cd src/backend
TRACING_ENABLED=false uv run pytest -m primary_data
```

Run seeded production-like scenario/integration tests:

```bash
cd src/backend
TRACING_ENABLED=false uv run pytest -m mocked_data
```

Run email-enabled integration tests:

```bash
cd src/backend
TRACING_ENABLED=false uv run pytest -m email_enabled
```

Run only full-system seeded scenarios:

```bash
cd src/backend
TRACING_ENABLED=false uv run pytest -m "mocked_data and scenario_flow"
```

Before commit use root `make verify-plan` / `make verify`; the commands above are explicit standalone scopes, not an unconditional checklist.

## 8.1) Seeded Full-System Scenario Sequence

File:
1. `tests/integration/scenarios/test_full_system_scenario.py`

Execution markers:
1. `mocked_data`
2. `scenario_flow`

Auth domain sequence (`test_seeded_auth_domain_main_flow`):
1. Seeded primary user login success
2. OAuth providers contract check
3. `/auth/me` success with bearer token
4. `/auth/admin/user-role-stats` success for seeded admin principal
5. `/auth/me` profile update success
6. `/auth/refresh` success with refresh context
7. `/auth/logout` success and session invalidation
8. `/auth/refresh` rejected after logout (`INVALID_TOKEN`)
9. `/auth/signup` duplicate email rejected (`EMAIL_ALREADY_EXISTS`)
10. `/auth/login` wrong password rejected (`INVALID_CREDENTIALS`)
11. `/auth/signup` malformed email rejected (422)
12. `/auth/resend-verification` contract success
13. `/auth/forgot-password` branch by `EMAIL_ENABLED` toggle

API key domain sequence (`test_seeded_api_key_domain_main_flow`):
1. Seeded primary user login success
2. `/api-keys` create success
3. Duplicate key name rejected (`API_KEY_NAME_ALREADY_EXISTS`)
4. `/api-keys` list includes created key
5. API key auth success on `/auth/me`
6. `/api-keys/{id}/status` disable success
7. Disabled key rejected on `/auth/me` (`API_KEY_INVALID`)
8. `/api-keys/{id}/status` enable success
9. Re-enabled key auth success on `/auth/me`
10. `/api-keys/{id}` delete success
11. Deleted key repeat-delete rejected (`API_KEY_NOT_FOUND`)

## 8.2) Test Data Lifecycle

1. `api_test` does not use DB seed data.
2. `primary_data` integration uses per-test isolated temporary DB with clean initial state.
3. `mocked_data` integration uses per-test isolated temporary DB plus seeded profile data.
4. Seed data is recreated for each test execution and discarded with temporary DB teardown.
5. `email_enabled` integration uses `email_enabled_integration_client` fixture which forces `EMAIL_ENABLED=true` with null mail provider to avoid external SMTP dependency.

## 8.3) Error Contract Consistency Rule (Static Serving Mode)

1. In static serving mode, SPA fallback must apply only to non-API HTML requests.
2. API-path (`/api/...`) 404 responses must preserve domain error payload shape from raised exception detail.
3. Do not replace API 404 detail with plain `"Not Found"` in fallback handler logic.

## 8.4) Current Scenario Inventory

Smoke:
1. `tests/test_smoke.py::test_ping_returns_ok`

API contract (`api_test`):
1. `tests/api/v1/auth/test_auth_api.py`
2. `tests/api/v1/api_key/test_api_key_api.py`
3. `tests/api/v1/events/test_events_api.py`

Integration primary dataset (`primary_data`):
1. `tests/integration/api/v1/auth/test_auth_integration.py` primary-state flows + RBAC forbidden/success branches
2. `tests/integration/api/v1/api_key/test_api_key_integration.py`

Integration email-enabled dataset (`email_enabled`):
1. `tests/integration/api/v1/auth/test_auth_integration.py` email verification required login + forgot-password token issuance flows

Integration seeded dataset (`mocked_data`):
1. `tests/integration/api/v1/auth/test_auth_integration.py` seeded-state flows
2. `tests/integration/scenarios/test_full_system_scenario.py`

## 9) Naming and intent

Use `test_<target>.py` and descriptive `test_<behavior>_<expected_result>` names.
Assert status, meaningful response fields and relevant domain error codes. Add a short
scenario docstring or Given/When/Then comments when they explain a non-obvious or
multi-step flow; trivial tests do not require boilerplate comments. Keep one behavior
owner per layer rather than copying the same negative case through every layer.

## 10) Change Checklist

When backend API behavior changes:
1. Update matching domain API tests under `tests/api/v1/<domain>/`.
2. Add/adjust smoke test only if boot/critical route contract changed.
3. If behavior depends on persistence semantics, add integration coverage.
4. Keep docs synchronized (`BACKEND.md`, `README.md`, this file if needed).

## 11) New domain verification

Use existing paths so the planner can find coverage without a new registry:
`tests/api/v1/<domain>/test_<domain>_api.py`, optional
`tests/integration/api/v1/<domain>/`, and unit tests named `test_<domain>*.py`.

- Cover the actual HTTP success contract. Add authentication/role/ownership failures
  for protected/private resources and validation failures when constrained input exists.
- A stateless input-free GET can be covered at the API layer; no empty-state DB test,
  seeded fixture, artificial 422 case or duplicate service test is required.
- Use integration tests when real persistence/query/transaction behavior matters.
  Keep representative stored-state/rollback/isolation invariants there; schema rejection
  belongs at the API/model layer and must not initialize DB/signup/login per invalid value.
- Existing-record-dependent behavior uses the smallest relevant SeedProfileSchema.
  `seeded_primary_client` supplies one principal for billing identity adoption;
  full-system scenarios retain primary+50 users and own seeded login/duplicate-email
  regression coverage. Auth/runtime changes always retain those broad scenarios.
- Update cross-domain scenarios only when the feature participates in that flow.
  Keep payload builders and seed profiles under existing fixture owners; never add real
  credentials/provider calls or production data to API contract tests.
- Before commit run root `make verify-plan` then `make verify`; record selected checks
  and any broad fallback. Static consumers/domain test paths select independent APIs;
  shared auth/permissions/ORM/migrations/config, unresolved imports or missing coverage
  keep the full backend suite. Test-only changes select the changed test files.
- App entry-point narrowing recognizes only constant, appended include_router wiring
  of newly added modules using the existing `from app.routers.v1 import ...` style.
  Other startup/lifecycle/registration changes remain broad.

## Shared Contract Regression Checks

`tests/test_openapi_contract.py` checks reference integrity, protected-route auth
responses, readiness 503, SSE/redirect transport declarations, both 500 envelopes,
and event data models. It runs under `api_test` without external services.
`make contract-check` separately checks freshness of the committed JSON baseline.

Mail template unit tests parse both EN/KO verification and reset HTML to verify
CTA/fallback URLs, plaintext preservation, locale and escaping of dynamic content.
They do not send mail or require a provider.

## Celery mail verification

Auth email integration tests capture Celery publication and assert the kind,
locale and issued token link without an external broker. Mail task tests cover
bounded retries, recovery, expiry, disabled mail and failure archive recovery.
Celery worker tests use an isolated memory transport; deployment fixtures execute
the real startup script with fake Docker commands to verify worker-before-API
ordering and fail-closed rollout. For release smoke, use isolated real Redis and a
local SMTP capture server, never customer email addresses or the production broker.

## Admin status checks

Admin status contract tests cover the role boundary, safe environment projection,
probe failure and timeout. Integration exercises actual SQLite/Redis probes and
immediate access loss after demotion with an existing token. The endpoint accepts
no parameters/body, so request validation (422) is not applicable. There are no
record-dependent aggregates or cross-domain mutations requiring seeded scenarios.

## Terminal display fixtures

Tests for an interactive Rich console explicitly set TERM with monkeypatch before
constructing the console. `force_terminal=True` alone does not override a dumb
terminal. Restore the caller environment automatically; do not require a global
terminal setting or change runtime fallback behavior to satisfy a fixture.

## Local tracing isolation

Run backend tests through root `make backend-test` (or `make verify`). These commands
set `TRACING_ENABLED=false` for the test process, independently of developer `.env`.
Tests must not start a real OTLP exporter; tracing-specific tests can opt in with a
mocked exporter. For direct pytest use `TRACING_ENABLED=false uv run python -m pytest`.
This also avoids forking a native gRPC exporter thread in subprocess-based deployment
fixtures on macOS. Production/runtime tracing settings are unchanged.
