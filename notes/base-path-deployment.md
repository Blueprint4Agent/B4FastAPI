# Monolithic deployment under a basePath

[한국어](ko/base-path-deployment.md)

A public basePath mounts the complete FastAPI + bundled React application beneath one
URL prefix. The default empty value (or `/`) preserves root deployment. The shared
Nginx server, DNS and TLS certificates remain operator-owned, outside each app stack.
No community/tracker/origin names are embedded in the implementation.

## Docker configuration

Set these public values in the copied project's `docker/.env` (example values only):

```dotenv
APP_BASE_PATH=/my-app
APP_BASE_URL=https://example.com/my-app
CORS_ORIGINS=https://example.com
VITE_PUBLIC_SITE_URL=https://example.com
APP_HOST_PORT=8001
COMPOSE_PROJECT_NAME=my-app
COMPOSE_FILE=docker-compose.yml
```

`APP_BASE_PATH` is the basePath setting. Use an absolute path containing only ASCII
letters, digits, `_`, `-` and single `/` separators; nested paths work. A trailing
slash is normalized away. URLs, query strings, fragments, percent encoding and dot
segments are rejected. CORS and `VITE_PUBLIC_SITE_URL` remain **origins without paths**.
Sharing metadata combines the public origin and build path automatically.

```sh
make docker-build
make docker-deploy
```

Compose passes `APP_BASE_PATH` to the image build; the Dockerfile supplies
`VITE_BASE_PATH` to Vite. The same runtime setting configures FastAPI. The image
contains the frontend in `app/static/dist`; no separate frontend server is needed.
For direct builds, pass `--build-arg APP_BASE_PATH=/my-app`. Prebuilt images must have
been built for the selected path. Changing a path requires rebuilding, not just
restarting. Startup rejects a packaged build whose `deployment-path.json` differs
from the runtime path. Existing root builds without that manifest remain compatible.

Do not enable the root-only Caddy HTTPS overlay for this topology. Keep each app's
Compose project, image tag, secrets and persistent data independent. App ports bind
loopback by default. If Nginx runs in a container, use a private shared Docker network
and the app's unique network alias on port 8000; `127.0.0.1` there means the Nginx
container, not the host. Do not publicly expose the upstream app ports.

## External Nginx

The supplied `docker/nginx/app-location.conf.template` is a reusable **server-block
fragment**, not an entire host/TLS configuration. Render one fragment per application:

```sh
export APP_BASE_PATH=/my-app
export APP_UPSTREAM=127.0.0.1:8001
envsubst '${APP_BASE_PATH} ${APP_UPSTREAM}' \
  < docker/nginx/app-location.conf.template > /tmp/my-app.locations.conf
```

Use a canonical nonempty path without a trailing slash in this fragment. Explicitly
listing the envsubst variables preserves Nginx variables such as `$http_host`.
Include the rendered fragment inside the existing `server` listening on HTTPS;
validate with `nginx -t` before reloading your Nginx service. DNS points the public
hostname to that server. Root deployments can use the existing root proxy setup.

The trailing slash in `proxy_pass` is required: `/my-app/api/v1/...` must reach the
upstream as `/api/v1/...`. FastAPI restores the external path for routing/redirect
URL generation. Do **not** additionally set Uvicorn `--root-path`, preserve the prefix
upstream, or rely on an untrusted `X-Forwarded-Prefix` header. Configure Uvicorn's
forwarded-header trust for the actual proxy address/network (especially container
networks), so OAuth callback URLs retain HTTPS. Set `FORWARDED_ALLOW_IPS` in
`docker/.env` to the actual private proxy IP or CIDR; its default is `127.0.0.1`.
Do not use `*` on an externally reachable upstream. Trust only a private proxy boundary.
The fragment streams SSE without buffering and keeps docs/metrics private. It does
not install DNS, certificates or a shared Nginx service for you.

## Local/manual monolithic packaging

Build and package with the equivalent frontend setting:

```sh
VITE_BASE_PATH=/my-app make frontend-package
```

Set `APP_BASE_PATH=/my-app` and the matching `APP_BASE_URL` in the backend environment,
then start the backend. Access it through the prefix-stripping proxy. A separate Vite
dev server uses `VITE_BASE_PATH` in `src/frontend/.env`; set `VITE_API_BASE_URL` to the
public **proxied** backend URL including its prefix. API-only development does not
require a frontend manifest. Desktop assets normally stay at `/`; configure their
`VITE_API_BASE_URL` to the remote backend URL including its public prefix.

## Authentication and validation

Browser storage keys and refresh cookie names are scoped by the canonical path.
Cookies are set and deleted at `<basePath>/`. Root deployments retain existing names
and keys. Changing the path requires signing in again; root session data is never
silently imported. Paths on one origin are not security isolation or shared sign-on.
Use independent secrets and data stores for independent applications.

Email links derive from `APP_BASE_URL`. Register OAuth callbacks including the prefix,
for example `https://example.com/my-app/api/v1/auth/oauth/google/callback`. Configure
Stripe return/webhook URLs with the prefix too when enabling billing; provider setup
is not automatic. Endpoint paths in the typed API contract remain app-relative.
The contract's documented cookie names describe the default root deployment.

Verify the public prefix redirect, a direct `/my-app/home` refresh, lazy routes, images,
`/my-app/config`, login/refresh/logout and SSE. Check another app's login remains
intact. Missing API/assets must remain 404 instead of returning the SPA. Internal
health checks still use `/health/ready`. `make docker-smoke` checks the direct upstream
and packaged assets; it does not certify an operator-owned external Nginx/TLS setup.

Public discovery documents, canonical links and sitemap entries use the configured
prefix. `/robots.txt` is origin-wide: the shared gateway owner must aggregate policy
and sitemap references at the domain root. A prefixed robots.txt is only a generated
artifact, not crawler policy for the whole hostname. Optional IndexNow submissions
must likewise be coordinated at the gateway; leave INDEXNOW_ENABLED=false for this
topology until its domain ownership configuration is established.

Run `make base-path-deployment-test` to build two disposable images and verify real
Nginx routing, browser navigation, SSE and cross-app session isolation. Requires Docker,
installed frontend dependencies and Playwright Chromium; test containers/networks/images
are cleaned up. Existing application stacks and volumes are untouched.
