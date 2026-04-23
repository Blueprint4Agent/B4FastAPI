# Blueprint4FastAPI

Blueprint4FastAPI is a full-stack template with:

- Backend: FastAPI + SQLAlchemy + Alembic + Redis
- Frontend: React + TypeScript + OpenAPI-generated API types
- Monolithic static serving support (frontend build copied into backend static path)

## Documentation Entry

1. Agent/workflow rules: `AGENTS.md`
2. Backend engineering rules: `src/backend/BACKEND.md`
3. Frontend engineering rules: `src/frontend/FRONTEND.md`
4. Backend quick guide: `src/backend/README.md`
5. Frontend quick guide: `src/frontend/README.md`

## Repository Layout

```text
src/
  backend/
  frontend/
docker/
scripts/
```

## Quick Start

1. Bootstrap env files:

```bash
pwsh ./scripts/bootstrap.ps1
```

or

```bash
bash ./scripts/bootstrap.sh
```

2. (Optional) Start local Postgres/Redis:

```bash
cd docker
docker compose --env-file .env up -d
```

3. Run backend:

```bash
cd src/backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

4. Run frontend:

```bash
cd src/frontend
npm ci
npm run dev
```

5. Open:

- Backend API docs: `http://localhost:8000/docs`
- Frontend app (Vite): `http://localhost:5173`

## Build

Backend:

```bash
cd src/backend
uv run ruff check . --fix
uv run ruff format .
```

Frontend:

```bash
cd src/frontend
npm run format
npm run build
```
