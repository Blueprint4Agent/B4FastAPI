# commit title

backend: add marker-based test matrix and full-system seeded scenarios

# changed file scope

- `src/backend/pyproject.toml`
- `src/backend/TEST.md`
- `src/backend/BACKEND.md`
- `src/backend/app/main.py`
- `src/backend/tests/conftest.py`
- `src/backend/tests/api/v1/auth/test_auth_api.py`
- `src/backend/tests/api/v1/api_key/test_api_key_api.py`
- `src/backend/tests/integration/api/v1/auth/test_auth_integration.py`
- `src/backend/tests/integration/api/v1/api_key/test_api_key_integration.py`
- `src/backend/tests/integration/scenarios/test_full_system_scenario.py`
- `src/backend/tests/fixtures/__init__.py`
- `src/backend/tests/fixtures/api_contract_data.py`
- `src/backend/tests/fixtures/payload_data.py`
- `src/backend/tests/fixtures/scenario_seed_data.py`
- `src/backend/tests/fixtures/scenario_flow_data.py`

# reason

- Separate API contract tests from primary integration tests and seeded production-like integration tests with explicit pytest markers.
- Establish a full-system seeded scenario flow that documents and verifies domain-by-domain API behavior under realistic preloaded data.
- Fix static serving mode 404 fallback to preserve API domain error payload contracts.

# impact

- Teams can run `api_test`, `primary_data`, and `mocked_data` suites independently while keeping full-suite execution as default.
- Full-system seeded scenario now verifies sequential auth and api-key success/failure branches from a pre-seeded principal user.
- API 404 responses under `/api/...` keep structured error details even when SPA static fallback is enabled.
