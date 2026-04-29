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
  integration/
    api/v1/
      auth/
        test_auth_integration.py
      api_key/
        test_api_key_integration.py
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
3. Request validation failure (422 when input invalid)

Notes for this codebase:
1. Router tests use fake services, not real repositories.
2. This keeps tests independent from DB and Redis runtime state.

## 6) Fixtures and Reuse

- Shared fixtures belong in `tests/conftest.py`.
- Current shared fixture: `sample_user` (`UserResponse`).
- Keep fixtures small and composable.
- If domain-only fixture is needed, define it near that domain test file.

## 7) Unit / Integration / E2E Policy

Unit tests:
1. Target service or utility decision logic.
2. Mock repository/external calls.
3. No real DB/network.

Integration tests:
1. Use real test DB/Redis path.
2. Isolate data per test (transaction rollback or dedicated reset fixture).
3. Cover flows where repository/query behavior matters.

E2E tests:
1. Run against a real running app instance.
2. Keep only critical user journeys.
3. Do not duplicate broad API contract coverage already done by lower levels.

## 8) Commands

Run all backend tests:

```bash
cd src/backend
uv run pytest
```

Run one file:

```bash
cd src/backend
uv run pytest tests/test_smoke.py
```

Run one domain:

```bash
cd src/backend
uv run pytest tests/api/v1/auth
```

Quality checks before commit:

```bash
cd src/backend
uv run ruff check .
uv run ruff format . --check
uv run pytest
```

## 9) Naming and Style Rules

1. File name: `test_<target>.py`
2. Test function name: `test_<behavior>_<expected_result>`
3. Each test function must include a one-line scenario docstring.
4. Multi-step tests must use `Given / When / Then` inline comments.
5. Use explicit assertions for:
   - status code
   - error code/message keys for domain failures
   - critical response payload fields
6. Keep each test focused on one behavior.

Required format template:

```python
def test_<behavior>_<expected_result>(...):
    """Scenario: <what flow is being verified in one sentence>."""
    # Given: <initial state or setup condition>
    # When: <action/request under test>
    # Then: <expected result/contract>
```

Example:

```python
def test_me_requires_authentication(sample_user):
    """Scenario: protected route denies access without auth dependency."""
    # Given: client without current-user override.
    # When: /api/v1/auth/me is requested.
    # Then: 401 with INVALID_TOKEN error code is returned.
```

## 10) Change Checklist

When backend API behavior changes:
1. Update matching domain API tests under `tests/api/v1/<domain>/`.
2. Add/adjust smoke test only if boot/critical route contract changed.
3. If behavior depends on persistence semantics, add integration coverage.
4. Keep docs synchronized (`BACKEND.md`, `README.md`, this file if needed).
