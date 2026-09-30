# Blueprint4FastAPI

Blueprint4FastAPI is a full-stack template with:

- Backend: FastAPI + SQLAlchemy + Alembic + Redis
- Frontend: React + TypeScript + OpenAPI-generated API types
- Optional desktop shell: Tauri 2 using the same React frontend
- Monolithic static serving support (frontend build copied into backend static path)

## Documentation Entry

1. Agent/workflow rules: `AGENTS.md`
2. Deployment guide: `DEPLOY.md`
3. Backend engineering rules: `src/backend/BACKEND.md`
4. Frontend engineering rules: `src/frontend/FRONTEND.md`
5. Backend quick guide: `src/backend/README.md`
6. Frontend quick guide: `src/frontend/README.md`
7. Shared API contract: `contracts/README.md` (`contracts/openapi.json`)

Localized documentation rule:

- Keep translated/localized docs under `notes/<locale>/...`.
- Mirror the original document structure by domain (`backend`, `frontend`, etc.).

Current locale example (`ko`):

1. Root guide: `notes/ko/README.md`
2. Agent/workflow rules: `notes/ko/AGENTS.md`
3. Deployment guide: `notes/ko/DEPLOY.md`
4. Backend engineering rules: `notes/ko/backend/BACKEND.md`
5. Frontend engineering rules: `notes/ko/frontend/FRONTEND.md`
6. Backend test guide: `notes/ko/backend/TEST.md`
7. Frontend test guide: `notes/ko/frontend/TEST.md`
8. Shared API contract: `notes/ko/contracts/README.md`

## Repository Layout

```text
contracts/
src/
  backend/
  frontend/  # B4React Git submodule
docker/
  scripts/
```

## Quick Start

1. Initialize env files:

```bash
make init
```

2. Run backend (local development):

```bash
make backend-install
make backend-dev
```

3. Run frontend (local development):

```bash
make frontend-install
make frontend-dev
```

4. Open:

- Backend API docs: `http://localhost:8000/docs`
- Frontend app (Vite): `http://localhost:5173`

## Make Workflow Hooks

Run `make help` to list the available workflow hooks.

Common targets:

```bash
make install              # Install backend and frontend dependencies
make backend-dev          # Run FastAPI development server
make frontend-dev         # Run Vite development server
make build                # Build backend environment and frontend artifacts
make test                 # Run backend and frontend tests
make check                # Check code, generated types, and API contracts
make format               # Format backend and frontend code
make ci                   # Run check, test, and build
```

Docker targets:

```bash
make docker-build
make docker-up
make docker-logs DOCKER_SERVICE=app
make docker-down
make docker-deploy
make docker-export
make docker-observability-up
make docker-observability-down
```

`make docker-observability-down` stops only Grafana, Prometheus, OpenTelemetry
Collector, Tempo, and Loki. The app, PostgreSQL, and Redis keep running. Stopped
containers and their data volumes are retained; use `make docker-observability-up`
to start the observability services again.

## Environment File Maintenance

```bash
make env-sync          # Update development env files (backend/frontend)
make env-check         # Check development env keys and layout
make docker-env-sync   # Update deployment env file (docker/.env)
make docker-env-check  # Check deployment env keys and layout
make env-contract-check # Check shared backend/Docker example keys only
```

Requires `uv`; development commands also require the initialized B4React submodule.
Each command uses the selected directories' `.env.example` files.
Sync rebuilds the file using the example's comments, blank lines, and key order,
preserving existing value tokens (including empty values, quoting, and escapes).
New keys receive example defaults. Local comments are replaced by example comments;
the original file remains in the backup. Additional keys are reported and retained
in a separate section at the end. Missing keys, duplicate keys, invalid syntax,
or outdated comments/layout fail the check.
Backend and Docker example keys must match, except the explicitly listed Docker-only
image, Compose project, host-port, metrics target, and Grafana login settings in `scripts/env.py`.
Values may differ by environment; their contents are never printed.

Add shared backend settings to both `src/backend/.env.example` and
`docker/.env.example`. `make env-contract-check` reports which example is missing
each key and fails on mismatches, without requiring actual `.env` files or the
frontend submodule. It also runs through `make check`, `make ci`, and local backend verification as a required validation step alongside lint/format checks. The regular
env commands enforce this same comparison; `docker-env-check` additionally catches
keys missing from the actual deployment `.env`. Frontend `VITE_*` settings are
separate. Keys present only in a local `.env` are reported as additional keys;
declare new shared settings in the examples to enforce deployment coverage.

Before changing an existing file, sync saves a timestamped backup under the root
`.env-backups/` directory, excluded from Git and Docker builds. Backups are readable
only by their owner. No backup is created for unchanged or newly created files.
Missing files are created from their examples. Comment-only and ordering changes
also trigger a sync and backup; unchanged files are not rewritten.

`make docker-deploy` (including direct execution of its script) runs `docker-env-check`
before building or recreating containers. Fix reported keys or run `make docker-env-sync`
and review new settings before retrying. This does not validate credentials,
connections, or settings in running containers. Docker deployment now also
requires `uv` for this check.

## Docker Deployment

### Project names and host ports

Container names are generated by Compose as `<project>-<service>-1`.
`COMPOSE_PROJECT_NAME=docker` preserves the original project's volume names; newly
created containers use names such as `docker-postgres-1`. Existing fixed-name
containers remain until explicitly recreated. Scripts use service names, so they
work with both naming styles. To start a separate installation, set a unique project
name and unused host ports in `docker/.env`, for example:

```dotenv
COMPOSE_PROJECT_NAME=b4fastapi
POSTGRES_HOST_PORT=5433
REDIS_HOST_PORT=6380
```

| Host-port setting | Default | Container port |
| --- | --- | --- |
| `APP_HOST_PORT` | 8000 | 8000 |
| `POSTGRES_HOST_PORT` | 5432 | 5432 |
| `REDIS_HOST_PORT` | 6379 | 6379 |
| `GRAFANA_HOST_PORT` | 3000 | 3000 |
| `PROMETHEUS_HOST_PORT` | 9090 | 9090 |
| `OTEL_GRPC_HOST_PORT` | 4317 | 4317 |
| `OTEL_HTTP_HOST_PORT` | 4318 | 4318 |

With the example above, the host backend uses `DB_PORT=5433` and `REDIS_PORT=6380`
in `src/backend/.env`; the Docker app keeps `DB_PORT=5432` and `REDIS_PORT=6379`.
When running multiple complete stacks, assign distinct values to every published
port and distinct `APP_IMAGE` tags if they use different builds. Adjust host-facing
URLs/CORS and local OTLP endpoints when their ports change. Set
`PROMETHEUS_BACKEND_TARGET` to the actual host backend port for local development;
the Docker app target remains `app:8000` regardless of `APP_HOST_PORT`.

Run `make docker-env-sync` to add the settings. Changing the project name creates a
separate stack with separate volumes; it does not rename or migrate existing data.
Keep `docker` for the current installation unless intentionally migrating. To apply
host-port changes to existing DB/Redis containers, explicitly recreate the affected
service as described below (`docker-up` preserves existing infrastructure).

### Database and observability access

#### Loki application logs

Logs follow `Python logging -> OTLP/gRPC -> Collector batch -> OTLP/HTTP -> Loki`.
The [native Loki OTLP endpoint](https://grafana.com/docs/loki/latest/send-data/otel/)
uses the existing Collector; no Docker socket or additional log agent is needed.

1. Run `make env-sync` for development or `make docker-env-sync` for deployment
   to add the new setting while preserving existing values (with a backup).
2. Set `LOGS_ENABLED=true` in `src/backend/.env` (host development) or `docker/.env`
   (Docker app). The default is false. It is independent of `TRACING_ENABLED`.
3. Use `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317` on the host, or
   `http://otel-collector:4317` in Docker. Adjust the host port if overridden.
4. Start the stack with `make docker-observability-up`. On an existing installation,
   reload the mounted Collector config and Grafana provisioning:

   ```bash
   docker compose -f docker/docker-compose.yml --env-file docker/.env --profile observability restart otel-collector grafana
   ```

5. Restart the development backend (`make backend-dev`), or rebuild/recreate the
   Docker app (`make docker-deploy`) to load the new dependency and settings.
6. Open Grafana **Explore → Loki**, select a recent time range, and run:

   ```logql
   {service_name="blueprint4fastapi-backend"}
   ```

This collects application/worker logs under `uvicorn.app`, Uvicorn server logs,
and access logs after setup, at the configured `LOG_LEVEL`. Console output remains.
It does not collect PostgreSQL/Redis/container stdout or arbitrary root loggers.
Request/task IDs are structured metadata, not index labels; filter with
`| request_id="..."` or `| task_id="..."`. Active OTel spans supply native trace
correlation; header/task fallback IDs do not guarantee a stored Tempo trace.
SDK batches flush on normal process exit; abrupt termination, queue overflow, or
prolonged collector outages can lose logs. This is not a durable audit log.

Before Loki starts, the one-shot `loki-init` service assigns the volume root to
UID/GID 10001, the Loki image user. An `Exited (0)` status for `loki-init` is normal.
This also repairs the root-owned volume created by the initial configuration;
existing data is preserved. Loki itself runs as its non-root image user.

Loki is a single instance with a `loki_data` volume and seven-day retention
(compactor deletion is asynchronous). Its unauthenticated API is only on the
Compose network at `loki:3100`, without a published host port. Grafana queries it
through the provisioned Loki datasource. This configuration targets a single host;
shared production deployments need storage/access policies appropriate to that environment.

#### Collector trace batching

The trace pipeline is `OTLP receiver -> batch processor -> Tempo/debug exporters`.
It uses Collector 0.114.0 defaults: a 200ms timeout and an 8192-span send trigger.
The trigger is not a maximum batch size. This combines incoming spans before
export independently of the backend SDK's existing `BatchSpanProcessor`.
See the [batch processor documentation](https://github.com/open-telemetry/opentelemetry-collector/blob/v0.114.0/processor/batchprocessor/README.md).

After changing the mounted Collector config, restart the running Collector to apply it:

```bash
docker compose -f docker/docker-compose.yml --env-file docker/.env --profile observability restart otel-collector
```

#### Prometheus target and shared network

App, Prometheus, Grafana, and the other Compose services already share the same
`<COMPOSE_PROJECT_NAME>_default` network. Keep the same project name for app and
observability commands; no external shared network is required.

Set one target in `docker/.env` after `make docker-env-sync`:

| Backend mode | PROMETHEUS_BACKEND_TARGET |
| --- | --- |
| `make backend-dev` on the host (default port) | `host.docker.internal:8000` |
| Host backend on port 8001 | `host.docker.internal:8001` |
| `make docker-up` in the same Compose project | `app:8000` |

Then run `make docker-observability-up` to apply the target. Enable
`METRICS_ENABLED=true` in the backend's active env file and restart/recreate the
backend if needed. The host backend must listen on an address reachable from Docker
(the default `make backend-dev` binds to `0.0.0.0`). A host-gateway mapping supports
host access on Linux too. The target contains only host:port; `/metrics` is configured
separately. Prometheus renders and validates its config at container startup.
The existing `b4fastapi-backend-local` job label is retained for dashboard/history
compatibility in both modes. Check target health at Prometheus's `/targets` page.

#### Database driver

`DB_NAME` depends on the driver. Change both fields when switching engines:

| Runtime | DB_DRIVER | DB_NAME | DB_HOST |
| --- | --- | --- | --- |
| Local SQLite (development default) | `sqlite+aiosqlite` | `template.db` (file) | Ignored |
| Host backend with Docker PostgreSQL | `postgresql+asyncpg` | `template` (database) | `localhost` |
| Docker app with Docker PostgreSQL | `postgresql+asyncpg` | `template` (database) | `postgres` |

For PostgreSQL, use an existing database name and matching credentials; the example
name `template` is created only on first initialization of the local DB volume.
`env-sync` preserves existing values, so changing the driver does not automatically
replace a SQLite file name with a PostgreSQL database name. Env checks do not verify
that the database exists. A `database "template.db" does not exist` error after
switching usually means the SQLite name was left in the PostgreSQL configuration.

- Local PostgreSQL initializes its user, password, and database from `DB_USER`,
  `DB_PASSWORD`, and `DB_NAME`. The app uses the same resolved credentials.
  Existing PostgreSQL volumes keep their existing accounts: changing `.env` alone
  does not change a database password. Update the database account separately;
  do not delete the volume to rotate credentials.
- A non-empty `REDIS_PASSWORD` enables password authentication on local Redis,
  the app connection, and its healthcheck. Empty remains supported for local
  development; configure a strong password for deployment. PostgreSQL still has
  a development default password, so set `DB_PASSWORD` for deployment as well.
- Database usernames/passwords and Redis passwords are URL-encoded by the backend.
  Enter the original password in `.env`, not a pre-encoded URL component. Quote
  literal values containing `$` with single quotes to prevent Compose interpolation.
- DB, Redis, Grafana, Prometheus, and OTLP host ports bind to `127.0.0.1`.
  Container-to-container traffic still uses Compose service names. Access from a
  remote workstation requires an SSH tunnel or a separately configured proxy.
  The app remains published on all host interfaces, using `APP_HOST_PORT` (default 8000).
- Tempo and Loki have no published host ports. Grafana queries `tempo:3200` and
  `loki:3100` on the Compose network. The Collector sends traces to `tempo:4317`
  and logs to `loki:3100/otlp`. The former `TEMPO_HOST_PORT` setting is unused
  and can be removed from existing `docker/.env` files.
- Grafana anonymous access is disabled. Run `make docker-env-sync`, then set
  `GRAFANA_ADMIN_PASSWORD` in `docker/.env` before `make docker-observability-up`.
  Grafana refuses to start with an empty password, `admin`, or `CHANGE_ME*`.
  `GRAFANA_ADMIN_USER` defaults to `admin`. These settings initialize new Grafana
  volumes; existing installations require changing the stored password through
  Grafana's UI or administrator CLI. Keep `.env` aligned with that password.

These settings take effect when containers are recreated. Env sync/check only
validates keys/layout; it does not rotate existing database or Grafana credentials.

1. Prepare env:

```bash
make init
```

2. Build app image:

```bash
make docker-build
```

3. Start services (`app` + optional local `postgres/redis` based on `docker/.env`):

```bash
make docker-up
```

Requires `uv` and Docker Compose with `up --wait --wait-timeout` support.
Infrastructure selection reads the app environment resolved by Compose, including
quoting, comments, interpolation, and service environment overrides. Existing
PostgreSQL/Redis containers are preserved with `--no-recreate`; missing containers
are created and stopped containers are started. Each startup stage waits up to
120 seconds by default (`HEALTH_TIMEOUT_SECONDS=180 make docker-up` to override).
The app healthcheck calls `/health/ready`, which checks both database and Redis.
Startup fails if services do not become healthy; it does not automatically roll back.

When intentionally changing local infrastructure credentials or configuration,
recreate only the affected service explicitly, then recreate/redeploy the app:

```bash
docker compose -f docker/docker-compose.yml --env-file docker/.env up -d --no-deps --force-recreate postgres
docker compose -f docker/docker-compose.yml --env-file docker/.env up -d --no-deps --force-recreate redis
```

Recreating PostgreSQL does not rotate credentials already stored in its data volume.

4. View logs:

```bash
make docker-logs DOCKER_SERVICE=app
```

5. Stop services:

```bash
make docker-down
```

6. One-shot deploy (env check + build + recreate app + wait for readiness + export tar):

```bash
make docker-deploy
```

Only the app is forced to recreate; existing local DB/Redis containers retain their
configuration. A readiness failure stops deployment before image export. Image
export uses Compose's resolved app image name, matching build rather than parsing
`APP_IMAGE` separately from `.env`.

7. Export app image tar:

```bash
make docker-export
```

Exported image files are stored in `docker/artifacts/`.

## Build

Backend:

```bash
make backend-format
make backend-test
```

Frontend:

```bash
make frontend-format
make frontend-build
```

The browser frontend remains the default. For optional local desktop development:

```bash
cd src/frontend
npm run tauri:dev
```

Or run it from the repository root. The launcher automatically adds the standard
Rust installation path (`~/.cargo/bin`) when the current shell has not loaded it:

```bash
make frontend-desktop-dev
```

## Shared frontend repository

B4React lives at [Blueprint4Agent/B4React](https://github.com/Blueprint4Agent/B4React)
and is pinned at `src/frontend`. Clone with `git clone --recurse-submodules`, or run
`make frontend-init` in an existing checkout. `make init` and `make frontend-install`
also initialize the committed pin.

- `make frontend-build`: produce only `src/frontend/dist`.
- `make frontend-package`: build and copy dist into backend static assets.
- `make build`: backend environment plus integrated frontend packaging.
- `make contract-check`: verify backend export and equality with B4React's local snapshot.
- `make frontend-api-check`: verify generated types without changing child files.

Frontend changes are reviewed and merged in B4React first. Update this repository's
submodule commit in a PR afterwards; do not track a moving branch in builds.
See [frontend integration](notes/frontend-submodule.md). Korean frontend source docs
are owned by B4React at `src/frontend/notes/ko/`; the old paths are entry links.

## Task workflow and PR checks

Read guides/status → create task branch → draft the [worklog](.github/WORKLOG_TEMPLATE.md)
→ implement → run Make checks → record results and stage files → validate governance
→ commit and open a PR. Record design, verification plan, loop alignment and actual outcomes.

With COMMIT_TITLE, `make git-governance-check` validates the staged snapshot and
COMMIT_BODY_FILE; without it, the command checks HEAD. Supply PR_TITLE and
PR_BODY_FILE together for planned PR validation. Untracked worklogs do not count.
Install local hooks with `make hooks-install` (included in `make init`). Commit messages and
staged worklogs are checked on commit; every outgoing authored commit and change-scoped
verification are checked on push. Actual PR metadata must be checked after edits and before
merge using `PR_NUMBER=<number> make git-governance-pr-check`. Integration merges are excluded.
Main requires PRs and resolved conversations and blocks deletion/force pushes. GitHub CI is
manual-only with no required status checks; zero required approvals remain.
See [local hooks](notes/local-hooks.md) · [한국어](notes/ko/local-hooks.md).

## Architecture checks

Run `make architecture-check` to validate the documented static layer boundaries.
It also runs in `make check` and local verification and optional manual CI. Errors include file/line locations.
Use `make backend-architecture-check` or `make frontend-architecture-check` for
a narrower scope. Backend routers delegate DB work to services; lower layers cannot
import routers/app.main. Frontend UI consumes page-owned hooks instead of runtime API
imports. Schema/Enum and explicit type-only imports are allowed. See the domain guides
for the precise static scope and limitations.

## API Key consistency

API Key UI notifications are best-effort. After a committed create/delete/status
change, Redis/OS/timeout delivery failures are logged without changing the success
response. Publication waits at most two seconds; cancellation and programming
errors still propagate. No durable event outbox/replay is provided.

The frontend useApiKeys hook owns list/mutation state. HTTP and SSE use the same
ID-based updates; server refetches reconcile events and mutation completion.
Connection/reconnection, developer-tab activation and desktop recovery reload the
list. Stale list/account responses are ignored. Modal/input/one-time key state stays
in SettingsPage; tab changes preserve a pending creation result. Background reloads
do not blank an already loaded list. Schema contracts remain unchanged.

## Operator role management

Assign roles to existing active accounts without adding a settings UI:

```sh
make user-role EMAIL=person@example.com ROLE=admin
make user-role EMAIL=person@example.com ROLE=user
```

This uses the backend environment (`src/backend/.env` and exported variables), not
`docker/.env`. For deployment, run inside the app container built with this command:

```sh
cd docker
docker compose exec app .venv/bin/python -m app.manage_user_role --email person@example.com --role admin
```

Run only against the intended database after migrations. The command creates no accounts
or tables, accepts `user`/`admin`, prints user ID and old/new roles, and rejects missing
or inactive users and demotion of the last active admin. Changes are serialized in
SQLite/PostgreSQL transactions. Output is an operator receipt, not a durable audit store.
Authorization uses the new DB role on subsequent requests; reload account data for UI badges.
`LOGIN_ENABLED=false` rejects this command because startup provisions a bootstrap admin.
Profile account switching/add-account actions are hidden when login is disabled or unknown.
Same-email Google/GitHub/email recent accounts display once using the latest login method; existing local duplicates normalize on read.

## Administrator panel

Administrators can open **Admin panel** from the profile menu (`/admin`). It uses
the settings-style sidebar and lists user identities, roles, account/verification
status, login methods, signup dates and latest successful login times. Search by
name/email, filter by role/status, page results or refresh manually. Bootstrap admins
can use it with login disabled; ordinary users cannot access its API or route.
Roles remain managed with `make user-role`. Active means enabled, not online.
No recorded login is shown explicitly; displayed times use the device time zone.

Frontend state management and React optimization policy: [English](src/frontend/notes/react-performance.md) · [한국어](src/frontend/notes/ko/react-performance.md). Use `make frontend-react-performance-check` for safeguards and `make frontend-test-routes` for production route recovery; both are included in local frontend verification.

## New project identity

Use [project initialization](PROJECT_SETUP.md) to configure a copied blueprint from `project.json`: service name, brand, desktop identifier and login/email/OAuth switches. Preview with `make project-plan`, apply with `make project-init`, and verify with `make project-check`. Korean guide: [새 프로젝트 초기화](notes/ko/PROJECT_SETUP.md).

## Local showcase style editing

Run `make backend-dev`, then `make frontend-style-studio` in another terminal.
Open `http://127.0.0.1:5173/show-case`. The compact right-hand panel previews common colors, radius, fonts and spacing in the existing showcase before applying them to local `src/frontend/src/styles/app.css`. Theme mode updates the global app preference. Color dropdowns and numeric controls follow the shared style; the header reload icon rereads the file. Set `FRONTEND_DIR=/absolute/path/to/B4React`
to run a compatible local frontend checkout instead. It must contain this editor's
Make target and installed dependencies. The target starts the selected checkout's
Vite server; it is not a remote server connection to a browser user's filesystem.

Normal `make frontend-dev` and production builds do not expose editing. Unsaved
preview is scoped to the showcase; apply creates a CSS backup in that frontend's
`.style-studio-backups/`, checks for external changes and triggers HMR. Changes
inside the pinned frontend are child-repository changes: review/commit through
B4React's own branch/PR workflow before updating the parent pin.

Search and pagination rules and usage: [English](notes/collections.md) · [한국어](notes/ko/collections.md).

Change-scoped verification: [English](notes/verification.md) · [한국어](notes/ko/verification.md).

## Celery

Standalone worker/Beat setup and migration audit: [English](src/backend/CELERY.md).
Korean guide: [한국어](notes/ko/backend/CELERY.md).
