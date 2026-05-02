# commit title

backend: add rbac role guard and admin stats endpoint with test harness coverage

# changed file scope

- `src/backend/alembic/versions/0005_users_role_rbac.py`
- `src/backend/app/models/user.py`
- `src/backend/app/core/error/auth_exception.py`
- `src/backend/app/deps.py`
- `src/backend/app/services/auth.py`
- `src/backend/app/routers/v1/auth.py`
- `src/backend/tests/conftest.py`
- `src/backend/tests/fixtures/scenario_seed_data.py`
- `src/backend/tests/fixtures/scenario_flow_data.py`
- `src/backend/tests/api/v1/auth/test_auth_api.py`
- `src/backend/tests/integration/api/v1/auth/test_auth_integration.py`
- `src/backend/tests/integration/scenarios/test_full_system_scenario.py`
- `src/backend/BACKEND.md`
- `src/backend/TEST.md`
- `src/backend/README.md`

# reason

- Introduce a baseline RBAC model with explicit user roles and a reusable dependency-based authorization guard.
- Provide a concrete admin-only endpoint so role checks are enforced and testable through API, integration, and scenario layers.
- Keep seeded test data and documentation aligned so future domains can reuse the same RBAC harness pattern.

# impact

- User domain now includes role information, persisted with DB migration and propagated through auth responses.
- Admin-only route (`/api/v1/auth/admin/user-role-stats`) now enforces `INSUFFICIENT_ROLE` for non-admin users.
- Backend tests now validate RBAC in api/primary/scenario paths, and docs define role-aware seed/schema conventions.
