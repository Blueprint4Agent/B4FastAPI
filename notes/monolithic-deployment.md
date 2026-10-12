# Monolithic server deployment

[한국어](ko/monolithic-deployment.md)

This is the initial production topology: browser → optional Cloudflare DNS/proxy →
Caddy HTTPS → one FastAPI container serving `/api/v1`, `/config` and the built React
SPA. PostgreSQL/Redis and optional mail workers run privately beside it, or the app
connects to existing external services. There is no separate frontend server.
Cloudflare DNS/proxy is the edge in this topology; the Docker origin still needs a
server such as AWS EC2. Frontend/backend separation and nginx configurations are
future work, not required for this monolith.

## 1. Prepare the server

Use a Linux host with Docker Engine and the Compose plugin, Python 3, Git and Make.
Compose must support `up --wait --wait-timeout` and `run --pull never`. Node, uv and
Python application dependencies are installed inside the Docker build. Allocate
persistent disk for Docker volumes and enough memory/disk for builds; use a tested
prebuilt image when the production host should not compile assets. Build/pull an
image matching the server's CPU architecture (for example EC2 arm64 vs amd64).

For AWS, assign a stable public address and configure security-group ingress for
TCP 80/443. Restrict SSH to operator addresses or use your configured management
channel. Do not open app port 8000, PostgreSQL 5432, Redis 6379 or observability
ports to the Internet. Review the [AWS security-group guide](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-rules-reference.html).

Create an A record (and an AAAA record only when IPv6 is actually configured) for
your hostname. For Cloudflare, initially use DNS-only to verify direct origin TLS;
after successful certificate issuance, enable the proxy if desired and use
[Full (strict)](https://developers.cloudflare.com/ssl/origin-configuration/ssl-modes/full-strict/).
Keep the origin certificate valid and its renewal challenge reachable. Do not use
Flexible mode with an HTTPS-redirecting origin. Avoid cache-everything rules on
`/api/*`, `/config`, `/health/*`, authenticated pages and SSE. Check login, OAuth,
webhooks and streaming again through Cloudflare; edge policies may affect them.

## 2. Initialize a fresh installation

```sh
git clone --recurse-submodules https://github.com/Blueprint4Agent/B4FastAPI.git
cd B4FastAPI
make docker-init PUBLIC_DOMAIN=app.example.com
```

Replace the example hostname with one you control. Initialization creates only a
**new** `docker/.env`, with mode 0600 and random signing/DB/Redis credentials. It
never prints credentials or replaces an existing file. This is ordinary .env
configuration; secret-file/secret-manager support is not introduced.

Review `docker/.env` on the server before deployment:

- Keep `APP_MODE=production` and `LOGIN_ENABLED=true`.
- Set a stable, installation-specific `COMPOSE_PROJECT_NAME` **before creating
  data**. Do not change it to perform an update; it selects networks/volumes.
- Set `APP_IMAGE` to the release tag you intend to build or deploy. Prefer explicit
  version tags or a registry digest for prebuilt releases, and retain the previous
  image reference for recovery.
- The default uses local PostgreSQL and Redis. For existing external services set
  their actual connection values; generated passwords do not modify those services.
- Email/OAuth/Stripe remain disabled until you configure and verify their provider
  settings. External storage also requires its own provider setup.
- For HTTPS the initializer aligns `PUBLIC_DOMAIN`, `APP_BASE_URL`, CORS and the
  public sharing origin, and persists
  `COMPOSE_FILE=docker-compose.yml:docker-compose.https.yml`.

For an existing installation, **do not regenerate keys**. Preserve project name,
credentials and data paths; edit the required values explicitly. The optional
`make docker-env-sync` developer tool requires uv and preserves existing values.
Backing up data and changing database account passwords are separate operations.
`docker-check` is a runtime preflight, not a comment/layout synchronization check.

An alternative file can be selected consistently with
`DOCKER_ENV_FILE=/absolute/path/production.env make docker-check` (and every other
core Docker command). Relative paths resolve from the caller's working directory.
Keep this file outside Git; do not commit `.env` contents. Shell environment values
take precedence in Compose interpolation, so clear stale `COMPOSE_FILE`,
`PUBLIC_DOMAIN`, `APP_IMAGE` overrides when switching deployments.

## 3. Check and deploy

```sh
make docker-check
make docker-deploy
make docker-status
```

`docker-check` resolves the actual Compose configuration without printing it,
rejects unsafe production placeholders and disposable SQLite paths, checks HTTPS
origin alignment, and confirms Docker daemon access. It does not contact external
providers or guarantee DNS/certificate issuance.

`docker-deploy` prepares the image, validates settings **inside that image**, then
waits for each selected stage: local DB/Redis → mail worker when enabled → API →
Caddy when selected. Existing DB/Redis containers are not recreated. App/worker/proxy
recreation can cause brief downtime on this single-instance topology. Do not run
concurrent deployments for the same project. Beat and observability remain opt-in;
if you operate them, update them explicitly with the same release and selected
configuration after checking their task/monitoring requirements.

Success additionally requires HTTP readiness, the expected runtime mode, a served
SPA and JavaScript asset, and blocked metrics/docs/OpenAPI routes behind Caddy. HTTPS
checks use normal certificate verification at the public origin; they do not disable
TLS checks. Each service wait and the HTTP retry window default to 120 seconds;
use `HEALTH_TIMEOUT_SECONDS=180 make docker-deploy` when needed. A failure exits
nonzero, does not report success and does not automatically roll back database
migrations. No image archive is created as a side effect.

Choose how the image is prepared:

```sh
make docker-deploy DEPLOY_SOURCE=build  # default; build this checkout
make docker-deploy DEPLOY_SOURCE=pull   # pull APP_IMAGE; authenticate to registry first
make docker-deploy DEPLOY_SOURCE=local  # use an already built/loaded image
```

For pull/local deployments, the image must contain this blueprint's runtime,
healthcheck and frontend assets. Build-time identity/sharing settings are already
embedded in a prebuilt image; changing .env on the server does not rebuild them.
Use `make docker-export` / `docker load -i <archive>` only for deliberate offline
image transfer. `make docker-build` prepares/validates an image without rollout;
`make docker-up` starts it without forced recreation or external HTTP smoke.

## 4. Operate, update and recover

```sh
make docker-status
make docker-smoke
make docker-logs DOCKER_SERVICE=app
make docker-logs DOCKER_SERVICE=caddy
```

Before an update, record the deployed image identity (`docker-status`), back up
PostgreSQL or SQLite and private object data, and confirm a tested restoration path.
Use the [database backup guide](../src/backend/DB_BACKUP_RESTORE.md). A Docker image
tar is **not** a database or object-data backup. Avoid `down -v`, Docker volume prune,
or changing the project name as an upgrade step.

Update to the reviewed parent revision, run `git submodule update --init --recursive`
to use its pinned child, and review release notes/migrations. Deploy the new explicit
image tag with the same environment/project. Run `docker-smoke`, then verify actual
login/refresh, configured email/OAuth/payment callbacks and SSE in a browser.
The healthcheck does not prove those external user journeys.

If rollout fails, inspect status and bounded logs. Existing infrastructure/data
are retained, but the previous API may already have been replaced. Choose a known
previous `APP_IMAGE` and deploy it with `DEPLOY_SOURCE=pull` or `local` only after
confirming schema compatibility. If a migration is incompatible, follow the tested
backup/restore procedure with writes stopped; do not blindly downgrade the image.
The deployment command never automatically restores databases or deletes volumes.

`make docker-down` stops the selected project and retains named volumes by default;
it is not the normal update command. All core commands honor the selected environment
and its Compose overlay list. See [Compose file selection](https://docs.docker.com/compose/how-tos/environment-variables/envvars/).

## Optional development support link

Set `VITE_BUY_ME_A_COFFEE_ENABLED=true` and `VITE_BUY_ME_A_COFFEE_URL=https://buymeacoffee.com/yourname` in the selected Docker environment, then run `make docker-deploy` to rebuild. The defaults disable the link. These values are public build arguments, not secrets. The B4A home and sidebar show the link only when server `APP_MODE=development`; production hides it even if enabled. A valid HTTPS creator profile is required; no third-party embed is loaded. Changing runtime environment without rebuilding does not change Vite build-time values.

The manual Build workflow accepts `coffee_enabled` (default false) and `coffee_url` as public frontend build arguments for GHCR images. These settings still never render support links when the server uses production mode. After merging, run the workflow with `ref=main` and `publish_image=true`; the published moving tag is `manual-main`.


## Public administrator demo

Set `DEMO_ENABLED=true` in `docker/.env`, then run `make docker-deploy DEPLOY_SOURCE=pull` with an image that includes this feature. The setting is runtime-only: no frontend rebuild is required. It defaults to `false` and works in production. `/config` reports `demo_enabled`.

Visitors, including guests, can open `/demo/admin` and `/demo/admin/server` from the profile dropdown (Admin panel (demo)) or the home previews. These reuse the administrator screens through GET-only `/api/v1/admin/demo/users` and `/api/v1/admin/demo/status`. Real administrator routes retain their role checks.

Opting in publishes real totals, roles, active/verified flags, login-provider names, day-level UTC signup/last-login dates and real server health/effective feature flags. Names, emails and database IDs are replaced with keyed pseudonyms; internal connection hosts and ports are removed. Search matches pseudonyms only. This is pseudonymized data, not a guarantee against inference from small populations. No credentials, IPs, profile data or mutation APIs are exposed. Results are cached per process for up to 30 seconds; errors fail closed. The first directory snapshot reads minimal projections of all users, so large deployments should assess memory usage before enabling this showcase feature.

Set `DEMO_ENABLED=false` and redeploy to remove navigation and return 404 from demo APIs. Do not rotate `SECRET_KEY` just to change aliases: it also signs authentication tokens. Demo mode does not enable metrics, tracing, log export or an observability stack.
