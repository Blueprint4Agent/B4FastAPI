# Refactor backend core package organization

## Commit Title

Refactor backend core package organization

## Changed File Scope

- Reorganized `src/backend/app/core/` into role-based packages:
  - `config/`
  - `db/`
  - `cache/`
  - `observability/`
  - `mail/`
- Updated backend imports, Alembic runtime imports, tests, and backend documentation.
- Centralized service exception handler registration for app and router-level API tests.
- Added SQLite runtime database ignore patterns for `src/backend/app/`.

## Reason

The previous `app/core/` directory mixed DB, Redis, settings, logging, metrics, tracing, health, mail, and migration files at one level, making the infrastructure responsibilities difficult to understand at a glance.

## Impact

- Backend infrastructure files are grouped by operational responsibility.
- Router boilerplate for service exception conversion is reduced through the shared app-level handler.
- Existing API error response contracts remain unchanged.
- Runtime SQLite artifacts generated under `src/backend/app/` are ignored by Git.

## Verification

- `uv run ruff check .`
- `uv run python -m pytest`
