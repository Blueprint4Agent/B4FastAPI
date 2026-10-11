# Commit Title

feat(deploy): unify monolithic server deployment

# Changed File Scope

Docker deployment command scripts, Make targets, Compose environment/HTTPS settings, env contract classification, deployment regression tests and English/Korean operator documentation.

# Reason

Provide a runnable single-server monolithic deployment path for AWS with optional Cloudflare DNS/proxy. Current deploy requires host uv, does not manage the HTTPS overlay consistently and always exports an image archive.

# Design

Use a dependency-free Python deployment entrypoint behind existing shell commands. Initialize only new private .env files, retain selected Compose files and env path across operations, validate resolved settings without disclosing values, build/pull/use a local image explicitly, start dependencies and worker before API and proxy, then verify HTTP behavior. Offer status/logs and separate optional image export. Preserve volumes and never automatically roll back migrations. Keep frontend packaged inside FastAPI; no frontend source or secret-file feature.

# Verification Plan

Root make verify-plan/make verify; subprocess regression tests for ordering, failure gates, environment selection, initialization preservation and no forced export; isolated real Compose deploy/update/readiness/persistence smoke without touching existing stacks. Validate HTTPS through existing local proxy probe and document public DNS/ACME as target-environment verification.

# Impact

New deployment uses Docker Compose and Python 3 on the host, with application dependencies inside the image. Persistent COMPOSE_FILE selects HTTPS across commands. Existing docker/.env is never overwritten by initialization. Downtime during single-instance recreation remains possible; no zero-downtime claim.

# Loop Alignment

Backend request/domain events unchanged. Deployment preserves mail worker readiness before API publishing. Frontend API/realtime/desktop/UI loops unchanged because the same packaged frontend is served by FastAPI. No component or state ownership changes.

# Verification

Root make verify-plan/make verify passed with backend=True/frontend=full classification: 459 backend tests, environment/architecture/contract checks, parent packaging and project-branding builds. Unchanged frontend check/test/UI/routes/Style Studio evidence was reused through content-bound receipts; no required checks were manually omitted. Focused deployment/mail subprocess and HTTP cases cover 18 scenarios, including selected env paths, failure-before-recreation, private init/no overwrite, proxy ordering and HTML Accept handling.

Real isolated Compose evidence: build and deploy with fresh PostgreSQL/Redis succeeded; local-image redeploy replaced the API while preserving PostgreSQL/Redis container IDs, a DB marker and a private object-file marker. Core status/smoke commands passed. Persisting the HTTPS overlay in the selected env started Caddy through the same up command; HTTPS was verified against the probe's local CA (no verification bypass), with SPA/signup/login, Secure/HttpOnly cookies and blocked metrics/docs/OpenAPI. Probe containers/networks/volumes were removed. AWS resources/public DNS/ACME were not provisioned or certified.

Initial real smoke exposed unsupported compose-run --no-build and the server's required Accept: text/html for SPA fallbacks; supported CLI options and browser-equivalent request headers now pass. The isolated probe's own direct-Compose cwd was corrected. Runtime loops remain unchanged except preserving the established mail-worker-before-API deployment ordering; no application state or request/domain event behavior changed.
