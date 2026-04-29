# commit title

backend: add integration auth/api-key tests and enforce test flow documentation style

# changed file scope

- `src/backend/tests/conftest.py`
- `src/backend/tests/test_smoke.py`
- `src/backend/tests/api/v1/auth/test_auth_api.py`
- `src/backend/tests/api/v1/api_key/test_api_key_api.py`
- `src/backend/tests/integration/api/v1/auth/test_auth_integration.py`
- `src/backend/tests/integration/api/v1/api_key/test_api_key_integration.py`
- `src/backend/TEST.md`

# reason

- Extend backend test coverage to integration-level API flows using real service and isolated test DB path.
- Improve test readability by standardizing scenario docstrings and Given/When/Then comments so flow intent is clear to contributors.

# impact

- Added integration coverage for signup/login/me and api-key issuance/access flow.
- Added duplicate email, invalid credentials, and validation error path checks in auth tests.
- Established mandatory test function documentation format in `TEST.md` for consistent team usage.
