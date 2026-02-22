# Blueprint4FastAPI

Blueprint4FastAPI is an internal project within the **BluePrint4Agent** organization.

This repository is a trimmed template focused on agent-driven customization patterns.

Included baseline features:
- Signup and authentication login
- JWT access token + Redis-backed refresh token rotation
- Initial project setup support (`.env`, DB, Redis)

Excluded from this template on purpose:
- Knowledge/topic/api-key/admin/rag modules
- MCP integration and non-auth business features

## Structure

```text
backend/
  app/
    core/        # settings, DB, Redis
    models/      # SQLAlchemy + API schemas
    services/    # auth business logic
    routers/v1/  # auth endpoints
    utils/       # password/token/cookie helpers
    main.py
frontend/
  src/
    api/         # HTTP client and auth API methods
    hooks/       # auth/session bootstrap logic
    pages/       # login/signup/dashboard
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
cd backend
pip install -e .
uvicorn app.main:app --reload --port 8000
```

4. Run frontend:
```bash
cd frontend
npm install
npm run dev
```

5. Open:
- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

## Environment Notes

- `backend/.env`
  - `DB_DRIVER=sqlite+aiosqlite` for zero-setup local DB
  - switch to `postgresql+asyncpg` for Docker/Postgres mode
  - `REDIS_IN_MEMORY=true` allows backend execution without external Redis
- `frontend/.env`
  - `VITE_API_BASE_URL` should point to backend host

## API Endpoints

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /ping`
- `GET /config`

## Agent-Focused Entry Guide

Read [`AGENT.md`](./AGENT.md) first.

## Frontend i18n

- i18n bootstrap: `frontend/src/i18n.ts`
- English locale file: `frontend/src/locales/en.json`
- Current default language: `en`
