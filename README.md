# Blueprint4FastAPI

Blueprint4FastAPI is an internal project within the **BluePrint4Agent** organization.

This repository is a trimmed template focused on agent-driven customization patterns.

Included baseline features:

- Signup and authentication login
- JWT access token + Redis-backed refresh token rotation
- Initial project setup support (`.env`, DB, Redis)

## Structure

```text
src/backend/
  app/
    core/        # settings, DB, Redis
    models/      # SQLAlchemy + API schemas
    services/    # auth business logic
    routers/v1/  # auth endpoints
    utils/       # password/token/cookie helpers
    main.py
docker/
  docker-compose.yml  # Postgres + Redis
scripts/
  bootstrap.ps1
  bootstrap.sh
```

## Quick Start

1. Bootstrap env files.

```bash
pwsh ./scripts/bootstrap.ps1
```

or

```bash
bash ./scripts/bootstrap.sh
```

2. (Optional) Run local infra:

```bash
cd docker
docker compose --env-file .env up -d
```

3. Run backend:

```bash
cd src/backend
pip install -e .
uvicorn app.main:app --reload --port 8000
```

4. Open:

- API docs: `http://localhost:8000/docs`

## Environment Notes

- `src/backend/.env`
    - `LOG_LEVEL=INFO` controls backend log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)
    - `DB_DRIVER=sqlite+aiosqlite` for zero-setup local DB
    - switch to `postgresql+asyncpg` for Docker/Postgres mode
    - `REDIS_IN_MEMORY=true` allows backend execution without external Redis
    - `LOGIN_ENABLED=false` disables all login entry points (`/api/v1/auth/login`, `/token`, OAuth login)
    - when `LOGIN_ENABLED=false`, backend also forces `OAUTH_ENABLED=false` and `EMAIL_ENABLED=false` (SMTP disabled)
    - when `LOGIN_ENABLED=false`, set only `BOOTSTRAP_USER_EMAIL` and `BOOTSTRAP_USER_NAME`; if that user does not exist, backend creates it on startup

## API Endpoints

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /ping`
- `GET /config`

## Agent-Focused Entry Guide

1. Read [`AGENTS.md`](./AGENTS.md) first.
2. For backend work, follow [`src/backend/BACKEND.md`](./src/backend/BACKEND.md).
