# Celery background execution

Celery 5.6 uses real Redis, independent of the API's `REDIS_IN_MEMORY` option.
This foundation does not migrate email, create billing tables, or charge customers.
The API continues running without a Celery worker; its readiness does not imply
Celery readiness. No result backend or periodic business tasks are enabled.

## Run locally

Run `make backend-install` and `make env-sync`. Start a real Redis instance.
Set `CELERY_BROKER_URL` in `src/backend/.env` if it differs from the API Redis;
an empty URL uses the existing encoded Redis host/port/database/password settings.
Use `rediss://` for a TLS broker. Do not put broker secrets in shell arguments.

In separate terminals:

```sh
make celery-worker
make celery-beat
make celery-ping
make celery-probe
```

The probe command prints a publication ID, not an execution receipt. Look for
`Celery probe completed` with that task ID in worker logs. Beat has an empty
schedule until a domain deliberately registers periodic work. Run exactly one
Beat per deployment. Local `solo` pool supports macOS development; use prefork on
Linux production (`CELERY_POOL=prefork CELERY_CONCURRENCY=2 make celery-worker`).
Solo cannot enforce process-based time limits and is not the production default.
Set `CELERY_BEAT_SCHEDULE` to a deployment-specific writable path for local Beat;
the default is `/tmp/b4fastapi-celerybeat`.

## Docker

Build the current application image with `make docker-build`, synchronize examples
with `make docker-env-sync`, and configure real Redis in `docker/.env`.
For the bundled broker, run `cd docker && docker compose up -d redis` first.
For an external broker, configure its URL instead. Then run from the repo root:

```sh
make docker-celery-up
# stop worker and Beat, preserving API and Redis
make docker-celery-down
```

The optional `celery` profile uses the same backend image with separate commands.
Worker uses prefork with two processes; Beat persists its schedule in a volume.
These targets do not implicitly start/replace databases or brokers. Existing
`docker-up`/`docker-deploy` only update the API: after rebuilding/deploying an image,
run `make docker-celery-up` to update these services as well. Keep API/worker images
compatible while rolling out tasks. Do not scale Beat. In containers, do not use
localhost for another container's Redis. Worker/Beat retries broker startup;
Compose's detached start alone is not a worker readiness check. Use inspect ping
and the probe via `docker compose exec celery-worker ./.venv/bin/celery -A
app.core.celery.app:celery_app ...` (replace `...` with `inspect ping` or
`call b4fastapi.probe`).

## Execution contract

- JSON only, UTC, dedicated configurable queue and Redis key prefix. Give each
  independent deployment unique `CELERY_QUEUE` and `CELERY_KEY_PREFIX` values when
  sharing Redis. Namespacing is not an access-control boundary.
- Late acknowledgment, worker-loss redelivery, prefetch one, 240/300-second soft/
  hard limits and 3600-second visibility timeout. Tasks must be idempotent.
  A repeatedly crashing task can be redelivered indefinitely: monitor and quarantine
  domain failures before adding production business tasks.
- Ordinary exceptions are not automatically retried. Define bounded retries for
  known transient domain failures. Celery has no equivalent of the existing mail
  DLQ in this foundation; add durable failure handling when migrating a domain.
- `await publish_task(name, payload=...)` runs synchronous broker publication in a
  thread, attaches task/trace IDs and redacts argument displays. Publication errors
  propagate for service-layer normalization. A timeout can be ambiguous; a task ID
  is not a deduplication guarantee. Broker payloads still contain the actual data.
- ContextTask isolates task log correlation; it does not propagate OTel spans.
  Existing HTTP OTel exporter initialization is not run in these separate processes.
- Persist future billing schedules and idempotency records in the application DB.
  Do not enqueue month-long countdowns. Beat should dispatch short due-work scans.
  DB commit plus broker publication needs an outbox/recovery strategy where loss
  is unacceptable. Redis AOF/backup/eviction policies also affect durability.
- Never use Celery acknowledgment as proof of exactly-once payment or SMTP delivery.

## Existing background work audit

| Current location | Decision | Migration requirements |
| --- | --- | --- |
| `core/task_queue/services/mail.py`: signup verification and password reset | First Celery migration candidates; unchanged in this commit | Keep async producer interface and EMAIL_ENABLED behavior; move consumer out of API lifecycle; preserve SMTP validation, locale, correlation, bounded retry and durable failure handling. |
| `core/task_queue/worker.py`: BRPOP, retry sleep, DLQ | Replace with Celery execution when mail migrates | Drain old `queue:mail:jobs` and inspect `queue:mail:dlq` before cutover; old envelopes are not Celery messages. Handle duplicate SMTP sends and expired token links. |
| `core/task_queue/bootstrap.py`, `main.py`: start/stop mail worker | Remove mail registration during migration | Roll out worker before switching producers; do not leave both competing implementations active. |
| `core/mail/service.py`: SMTP `asyncio.to_thread` | Execution helper, not scheduler | Can run inside a Celery task; keep async API until domain migration is implemented. |
| `core/realtime/sse.py`: stream heartbeat and Redis subscription | Keep in FastAPI | Connection-bound streaming/cancellation must remain with the HTTP request. |
| Startup DB migration, SMTP validation and readiness checks | Keep lifecycle responsibilities | Deployment readiness depends on their completion; not fire-and-forget jobs. |

No other application `create_task` or FastAPI `BackgroundTasks` jobs were found.
No current recurring billing/cleanup scheduler exists to migrate.

References: [Celery Redis delivery caveats](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html),
[periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html).
