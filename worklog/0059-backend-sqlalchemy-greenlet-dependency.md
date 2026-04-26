# 0059 Worklog

- Commit title: `fix: add greenlet dependency for async sqlalchemy startup`
- Scope: `backend-deps`

## Changed Files

- `src/backend/pyproject.toml`
- `src/backend/uv.lock`

## Reason

- Backend startup failed when initializing async SQLAlchemy engine because `greenlet` was not installed.
- Ensure required runtime dependency is explicitly declared instead of relying on transitive installation behavior.

## Impact

- Prevents startup failure (`No module named 'greenlet'`) during DB initialization.
- Improves cross-platform consistency for backend runtime dependency resolution.
