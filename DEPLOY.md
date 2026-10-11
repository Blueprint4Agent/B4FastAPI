# Deployment Guide

This document defines the concrete deployment flow for this repository.

## 1) Prerequisites

1. Docker Desktop (or Docker Engine) is installed and running.
2. Repository root is current working directory.
3. Ports are available when using local infra:

- `8000` (app)
- `5432` (postgres)
- `6379` (redis)

Git, Make and Python/uv are also required. Compose must support `up --wait --wait-timeout`.
Local frontend builds need Node.js 24 and npm; Docker builds run these inside the image.

## 2) Environment Setup

Initialize template env files:

```bash
make init
```

Primary deployment env file:

- `docker/.env`

Before deployment, set a unique random `SECRET_KEY` in `docker/.env`.
Generate one with `python3 -c "import secrets; print(secrets.token_urlsafe(48))"`.
Review DB/Redis passwords, public APP_BASE_URL/CORS_ORIGINS and enabled integrations.
Do not automatically replace existing keys; see [production key policy](notes/runtime-modes-rbac.md).

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
DB_NAME=/var/lib/b4fastapi/database/template.db

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

## 5) GitHub Actions build pipeline

`.github/workflows/build.yml` runs only through manual `workflow_dispatch`.
PRs, pushes, tags, releases and schedules do not automatically run it. Local hooks
perform verification; PR protection is separate from server-side test enforcement.

- `ref`: branch, tag or commit SHA; `pr_number` takes precedence as `refs/pull/<number>/head`.
- `publish_image=false` (default): backend/frontend validation only.
- `publish_image=true`: validate, build and push the selected image to
  `ghcr.io/<owner>/<repo>`; when neither ref nor PR is supplied, select `main`.
- Published tags are `manual-<sanitized-ref>` (for example `manual-main`),
  `manual-pr-<number>` for PR selection, and a short SHA tag. There is no automatic
  `nightly-main` or release/version image publishing.

Backend and frontend jobs use full verification. The frontend checkout includes
its pinned submodule recursively. Manual publication is an explicit operation;
select the intended revision before starting it.

## 6) Desktop build pipeline

`.github/workflows/desktop-build.yml` also runs only through manual `workflow_dispatch`.
It has no automatic schedule, release or tag trigger.

| Platform | Runner | Rust target |
| --- | --- | --- |
| macOS Apple Silicon | macos-14 | aarch64-apple-darwin |
| macOS Intel | macos-15-intel | x86_64-apple-darwin |
| Linux x64 | ubuntu-22.04 | runner default |
| Windows x64 | windows-latest | runner default |

`api_base_url` takes precedence over `DESKTOP_API_BASE_URL`, then falls back to
`http://localhost:8000`. Set the deployed API origin for a distributable build.
The value is embedded as `VITE_API_BASE_URL`; desktop builds do not bundle the backend.

Installers/bundles are retained as Actions artifacts for 14 days. A manually selected
tag ref supplies release metadata to the Tauri action; an ordinary branch run does
not create a tagged release. Current artifacts are unsigned. Public distribution
still requires appropriate signing/notarization and installation verification.

## 7) Post-Deploy Verification

Check running containers:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

Check app health endpoints:

```bash
curl --fail http://localhost:8000/health/live
curl --fail http://localhost:8000/health/ready
curl -i http://localhost:8000/config
```

Check startup migration log:

- `Database schema migration check complete (target=head).`

## 8) Troubleshooting

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

## Frontend source and packaging

Initialize the pinned B4React submodule before local Docker builds (`make frontend-init`).
Build and desktop workflows use recursive checkout. The frontend build writes only
its own dist; the parent Dockerfile copies it into FastAPI static assets.
For local integrated serving use `make frontend-package` or `make build`.
B4React owns frontend source and its local contract. A submodule update must pass
provider snapshot, consumer snapshot, and generated type checks. Desktop bundle
identity is preserved during this extraction.

## SQLite persistence and existing deployments

SQLite uses the `sqlite_data` named volume mounted at `/var/lib/b4fastapi/database`
in both the API and worker. `docker-up` rejects paths outside this directory, including
relative paths and `..` traversal, before starting/recreating services. In-memory Redis
is not durable or shared between API processes; use real Redis for multi-process use.
PostgreSQL remains the default deployment database.

For an existing SQLite container, stop writes and workers, back up the database using
SQLite's backup facility, and copy the backup out **before** recreating/removing the old
container. Import that backup into the new volume and set the absolute `DB_NAME` above;
verify accounts and the current Alembic revision before reopening traffic. Merely changing
DB_NAME creates a different database; deployment does not automatically migrate old files.
Keep the Compose project name stable, and do not run `docker compose down -v` when
preserving data. See [backup/restore](src/backend/DB_BACKUP_RESTORE.md).

## Public HTTPS deployment and container permissions

The app/worker/Beat image runs as UID/GID `10001:10001`, with no Linux capabilities
and no privilege escalation in Compose. Fresh named data volumes inherit writable
image directory ownership. Existing root-owned local-object, SQLite and Beat volumes
must be backed up and explicitly migrated to UID/GID 10001 before upgrading. Review
the selected volume names and any custom OBJECT_STORAGE_LOCAL_ROOT first; this
repository does not recursively change ownership of existing data automatically.

The base app port is published on `127.0.0.1` only. For public access, point your DNS
to the server, permit inbound TCP 80/443, and configure the production signing key,
APP_BASE_URL and CORS_ORIGINS with the actual HTTPS origin. Update enabled OAuth
callback and Stripe return/webhook URLs accordingly. Set SWAGGER_ENABLED=false if
API documentation is not needed. Keep database passwords unique.

Use the optional proxy after the app passes local readiness:

```sh
make docker-build
make docker-up
cd docker
export PUBLIC_DOMAIN=app.example.com  # replace with a hostname you control
docker compose --env-file .env -f docker-compose.yml -f docker-compose.https.yml config --quiet
docker compose --env-file .env -f docker-compose.yml -f docker-compose.https.yml up -d --no-deps --wait app caddy
```

Keep PUBLIC_DOMAIN exported and both Compose files selected for later public
rollouts; the plain `make docker-deploy` command does not manage this optional
overlay and would remove its app proxy-trust setting when recreating the app.
Build with `make docker-build` from the repository root, then repeat the combined
Compose command. Start required DB/Redis/mail workers through the normal startup
flow first; this command deliberately does not recreate infrastructure.

Caddy manages TLS certificates and blocks public metrics, Swagger/Redoc and
OpenAPI routes. Prometheus can still scrape `app:8000` privately. The proxy streams
SSE without response buffering. The overlay lets Uvicorn trust forwarded headers
from this private network so OAuth redirects use HTTPS. Do not expose the app port
on all interfaces or attach untrusted workloads to that network.

Verify the deployed domain with `/health/ready`, login/refresh cookies and OAuth
redirects. Confirm `/metrics` is unavailable publicly. Local TLS smoke tests do not
prove public DNS, certificate issuance, provider callbacks or backup recovery.
See [Caddy proxy documentation](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).
