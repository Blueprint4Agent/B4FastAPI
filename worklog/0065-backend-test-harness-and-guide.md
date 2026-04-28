# commit title

backend: add smoke/api test harness and test engineering guide

# changed file scope

- `src/backend/tests/conftest.py`
- `src/backend/tests/test_smoke.py`
- `src/backend/tests/api/v1/auth/test_auth_api.py`
- `src/backend/tests/api/v1/api_key/test_api_key_api.py`
- `src/backend/TEST.md`
- `src/backend/BACKEND.md`
- `src/backend/README.md`
- `src/backend/pyproject.toml`
- `src/backend/uv.lock`

# reason

- Establish a de-facto backend test baseline with fast smoke and API contract tests by domain.
- Document explicit backend test engineering rules aligned with `src/backend/BACKEND.md`.

# impact

- Added runnable smoke test for app boot and `/ping` contract.
- Added domain API contract tests for `auth` and `api_key` using dependency overrides.
- Added backend test guidance document (`src/backend/TEST.md`) and linked it from backend docs.
- Added pytest/httpx dev dependencies and pytest discovery settings for consistent local/CI execution.
