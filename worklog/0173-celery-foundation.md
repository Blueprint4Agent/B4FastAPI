# Commit Title

feat(backend): add Celery worker and scheduler foundation

# Changed File Scope

Backend Celery configuration and diagnostic task, settings/examples/lockfile,
root Make targets, optional Docker services, tests, EN/KO documentation.

# Reason

Prepare independent background execution for the subscription template and audit
existing background work before choosing a billing provider.

# Design

Add a standalone Celery application with a real Redis broker, JSON messages,
UTC, bounded task execution and a dedicated queue. Worker and singleton Beat run
outside FastAPI. Beat starts with no business schedules. Add an explicit harmless
probe task and publish helper that propagates trace context without blocking the
async request loop. Keep result storage disabled. Docker services are opt-in.
Audit the legacy mail queue, retry/DLQ behavior and SSE lifecycle; migration of
mail producers/consumers is a follow-up, not part of this infrastructure request.
No HTTP contract, ORM or database schema changes.

# Verification Plan

Root make verify-plan and make verify; unit tests and a real Celery worker test
using an isolated in-memory transport; real Redis process smoke if available;
Compose structural validation; staged Git governance and PR checks.

# Impact

No existing mail or API behavior switches. Real Redis is required for standalone
Celery even when the API uses fakeredis. At-least-once delivery requires domain
idempotency; no billing jobs or production charges are introduced.

# Loop Alignment

Request lifecycle remains unchanged; future async producers use the publish helper.
Background execution is owned by standalone Celery; Beat owns periodic dispatch.
SSE remains in the request lifecycle; no domain event changes. Frontend loops are
not applicable because no frontend runtime or contract changes are made.

# Verification

- `make verify-plan`: backend checks plus full frontend/integration scope because
  Makefile, Compose, settings and dependencies are protected changes.
- `make verify`: all seven selected groups passed: root tooling/architecture/env,
  backend lint/tests/contracts, frontend checks/tests, browser UI, production routes,
  style studio, contract/package integration and project branding build checks.
- Final type annotations were added after the backend group completed;
  `make backend-check backend-test` passed again (87 tests, 3 existing deprecation
  warnings). Unchanged frontend checks were not repeated.
- Isolated real Redis 7 Docker container and separate Celery processes: worker
  startup/ping, async publication with task/trace logging and Beat dispatch of a
  temporary one-second probe schedule all passed. Processes/container were removed.
- Compose model validated with the example environment (`config --quiet`).
- Celery 5.6.3 resolves redis-py to 6.4.0 (from 7.2.1); full backend Redis/auth/mail
  regressions passed. Production lockfile remains synchronized with uv.
- No selected checks omitted. Production Docker image rollout was not performed:
  configuration is opt-in and no live stack or existing mail queue was changed.
  Process smoke used local solo; Linux prefork deployment is configured but not
  exercised as a deployed application image.
- Git governance is validated against the staged commit and planned PR metadata.
  No backend/frontend loop was intentionally bypassed; non-applicable loops and
  the explicitly deferred mail cutover are described above.
