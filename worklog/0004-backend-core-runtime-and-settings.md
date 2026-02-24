# 0004 Worklog

- Commit title: `feat: scaffold backend runtime and core settings`
- Scope: `backend`

## Changed Files

- `backend/pyproject.toml`
- `backend/uv.lock`
- `backend/.env.example`
- `backend/.flake8`
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/deps.py`
- `backend/app/core/__init__.py`
- `backend/app/core/settings.py`
- `backend/app/core/database.py`
- `backend/app/core/redis.py`
- `worklog/0004-backend-core-runtime-and-settings.md`

## Reason

- Establish executable FastAPI app entrypoint and lifecycle.
- Centralize environment-driven configuration for app, DB, and Redis.
- Provide async DB session and Redis client management primitives.

## Impact

- Backend can start in local mode with `.env`-driven settings.
- Core infra layer is ready for auth domain and API routes.
