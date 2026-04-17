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
src/frontend/
  src/
    api/         # OpenAPI-generated types + typed HTTP client
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
cd src/backend
pip install -e .
uvicorn app.main:app --reload --port 8000
```

4. Run frontend:

```bash
cd src/frontend
npm install
npm run dev
```

5. Open:

- Frontend: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`

## Environment Notes

- `src/backend/.env`
    - `DB_DRIVER=sqlite+aiosqlite` for zero-setup local DB
    - switch to `postgresql+asyncpg` for Docker/Postgres mode
    - `REDIS_IN_MEMORY=true` allows backend execution without external Redis
    - `LOGIN_ENABLED=false` disables all login entry points (`/api/v1/auth/login`, `/token`, OAuth login)
    - when `LOGIN_ENABLED=false`, backend also forces `OAUTH_ENABLED=false` and `EMAIL_ENABLED=false` (SMTP disabled)
    - when `LOGIN_ENABLED=false`, set only `BOOTSTRAP_USER_EMAIL` and `BOOTSTRAP_USER_NAME`; if that user does not exist, backend creates it on startup
- `src/frontend/.env`
    - `VITE_API_BASE_URL` should point to backend host

## Frontend OpenAPI Contract

- Source of truth: backend OpenAPI endpoint `http://localhost:8000/openapi.json`
- Generated file: `src/frontend/src/api/generated/openapi.ts`
- Primary command:
    - `npm run generate:api`
- Build behavior:
    - `npm run build` runs `generate:api` first, then TypeScript/Vite build
- Optional safe sync:
    - `npm run generate:api:optional`
    - If regeneration fails but a generated file already exists, the build can continue with the existing file

Guideline:

- Frontend API code should import contract types from `src/api/generated/openapi.ts`.
- Avoid adding hand-written API contract types for endpoints already present in OpenAPI.

## API Endpoints

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /ping`
- `GET /config`

## Agent-Focused Entry Guide

Read [`AGENTS.md`](./AGENTS.md) first.

## Frontend i18n

- i18n bootstrap: `src/frontend/src/i18n.ts`
- English locale file: `src/frontend/src/locales/en.json`
- Current default language: `en`

## Show Case + Agent Workflow

- Open the Show Case page after login: `http://localhost:5173/show-case`
- Review available UI components by category (`Buttons & Components`, `Cards`)
- Ask the Agent to compose UI by explicitly naming components from Show Case
- Example prompt:
    - "Build the settings form with `PanelCard`, `InputField`, `FormCheckbox`, `Button`, and `InfoCard`."
- Prefer component-first requests over raw HTML/CSS requests for consistency and reuse.
