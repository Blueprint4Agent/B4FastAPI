# Deployment Guide

This document defines the concrete deployment flow for this repository.

## 1) Prerequisites

1. Docker Desktop (or Docker Engine) is installed and running.
2. Repository root is current working directory.
3. Ports are available when using local infra:

- `8000` (app)
- `5432` (postgres)
- `6379` (redis)

## 2) Environment Setup

Initialize template env files:

```bash
bash ./docker/scripts/init-env.sh
```

Primary deployment env file:

- `docker/.env`

## 3) Deployment Modes

`docker/scripts/docker-up.sh` decides whether local `postgres`/`redis` containers are started.
When local infra is selected, it now waits for container health before starting `app`.

### Mode A: App + Local Postgres + Local Redis

Use this in `docker/.env`:

```dotenv
DB_DRIVER=postgresql+asyncpg
DB_HOST=postgres
DB_PORT=5432
DB_NAME=template
DB_USER=postgres
DB_PASSWORD=postgres

REDIS_IN_MEMORY=false
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

Result:

- Starts: `app`, `postgres`, `redis`

### Mode B: App + External Postgres + External Redis

Use this in `docker/.env`:

```dotenv
DB_DRIVER=postgresql+asyncpg
DB_HOST=<external-db-host>
DB_PORT=5432
DB_NAME=<db-name>
DB_USER=<db-user>
DB_PASSWORD=<db-password>

REDIS_IN_MEMORY=false
REDIS_HOST=<external-redis-host>
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<optional>
```

Result:

- Starts: `app` only

### Mode C: App + SQLite + In-Memory Redis

Use this in `docker/.env`:

```dotenv
DB_DRIVER=sqlite+aiosqlite
DB_NAME=template.db

REDIS_IN_MEMORY=true
```

Result:

- Starts: `app` only

## 4) Standard Commands

Build app image:

```bash
bash ./docker/scripts/docker-build.sh
```

Start services:

```bash
bash ./docker/scripts/docker-up.sh
```

Stop services:

```bash
bash ./docker/scripts/docker-down.sh
```

Follow logs:

```bash
bash ./docker/scripts/docker-logs.sh app
```

One-shot deploy (build + recreate up + export tar):

```bash
bash ./docker/scripts/docker-deploy.sh
```

Export image tar only:

```bash
bash ./docker/scripts/docker-export.sh
```

Export path:

- `docker/artifacts/`

## 5) GitHub Actions Build Pipeline

Workflow:

- `.github/workflows/build.yml`

Triggers:

- Pull requests targeting `main`
- Nightly build of `main` at `00:00 KST` (`15:00 UTC`)
- Manual `workflow_dispatch` with optional `ref` or `pr_number`
- Release published events
- Version tag pushes matching `v*`
- No Docker image is built automatically for every `main` merge.

Manual `ref` examples:

- `main`
- `v1.0.0`
- `<commit-sha>`

Manual PR build example:

- `pr_number=12` builds `refs/pull/12/head`

Pipeline jobs:

- Backend: `uv sync --frozen`, Ruff check, Ruff format check, Pytest
- Frontend: `npm ci`, Prettier check, Vitest, production build
- Docker: build image from `docker/Dockerfile` only for release/tag, schedule, or explicit manual publish runs

Image publishing:

- Pull request builds validate backend/frontend checks only.
- Scheduled runs publish the `main` image as `nightly-main`.
- Default manual runs validate backend/frontend checks only.
- Manual runs publish the selected ref image only when `publish_image=true`.
- Manual image publishing defaults to the `main` ref and `main` image tag when both `ref` and `pr_number` are empty.
- Manual image publishing with `ref=main` also uses the `main` image tag.
- Release published events and `v*` tag pushes publish to GitHub Container Registry.

Default image registry:

- `ghcr.io/<owner>/<repo>`

## 6) Post-Deploy Verification

Check running containers:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

Check app health endpoints:

```bash
curl -i http://localhost:8000/docs
curl -i http://localhost:8000/config
```

Check startup migration log:

- `Database schema migration check complete (target=head).`

## 7) Troubleshooting

`docker command not found`

- Install Docker Desktop/Engine and ensure Docker daemon is running.

App starts but DB connection fails

- Confirm `DB_DRIVER/DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD` in `docker/.env`.
- If using local postgres, `DB_HOST` must be `postgres`.

Redis connection fails

- For local redis container: `REDIS_IN_MEMORY=false` and `REDIS_HOST=redis`.
- For external redis, set `REDIS_HOST` to external host and keep `REDIS_IN_MEMORY=false`.

Alembic startup migration fails with revision length errors

- Keep Alembic `revision` IDs short enough for `alembic_version.version_num` constraints.

No tar artifact found

- `docker-build.sh` does not export tar.
- Use `docker-deploy.sh` or `docker-export.sh`.
