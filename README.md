# Blueprint4FastAPI

Blueprint4FastAPI is a full-stack template with:

- Backend: FastAPI + SQLAlchemy + Alembic + Redis
- Frontend: React + TypeScript + OpenAPI-generated API types
- Monolithic static serving support (frontend build copied into backend static path)

## Documentation Entry

1. Agent/workflow rules: `AGENTS.md`
2. Deployment guide: `DEPLOY.md`
3. Backend engineering rules: `src/backend/BACKEND.md`
4. Frontend engineering rules: `src/frontend/FRONTEND.md`
5. Backend quick guide: `src/backend/README.md`
6. Frontend quick guide: `src/frontend/README.md`

## Repository Layout

```text
src/
  backend/
  frontend/
docker/
  scripts/
```

## Quick Start

1. Initialize env files:

```bash
bash ./docker/scripts/init-env.sh
```

2. Run backend (local development):

```bash
cd src/backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

3. Run frontend (local development):

```bash
cd src/frontend
npm ci
npm run dev
```

4. Open:

- Backend API docs: `http://localhost:8000/docs`
- Frontend app (Vite): `http://localhost:5173`

## Docker Deployment (Bash Only)

1. Prepare env:

```bash
bash ./docker/scripts/init-env.sh
```

2. Build app image:

```bash
bash ./docker/scripts/docker-build.sh
```

3. Start services (`app` + optional local `postgres/redis` based on `docker/.env`):

```bash
bash ./docker/scripts/docker-up.sh
```

4. View logs:

```bash
bash ./docker/scripts/docker-logs.sh app
```

5. Stop services:

```bash
bash ./docker/scripts/docker-down.sh
```

6. One-shot deploy (build + recreate + export tar):

```bash
bash ./docker/scripts/docker-deploy.sh
```

7. Export app image tar:

```bash
bash ./docker/scripts/docker-export.sh
```

Exported image files are stored in `docker/artifacts/`.

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
