# Celery background execution

Celery 5.6 uses real Redis, independent of the API's `REDIS_IN_MEMORY` option.
Signup verification and password-reset emails now execute in Celery.
Email-enabled installations require a standalone worker; the API readiness endpoint
does not imply Celery readiness. No billing tables or payment execution are added.
No result backend or periodic business tasks are enabled.

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
`Celery probe completed` with that task ID in worker logs. Beat scans the lifecycle mail outbox every minute. Run exactly one
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
These explicit targets do not implicitly start/replace databases or brokers.
`docker-up`/`docker-deploy` now start/update and health-check the worker before the
API when both LOGIN_ENABLED and EMAIL_ENABLED are true. They also start the bundled
Redis if it is the mail broker, even when the API uses fakeredis. A worker health
failure stops the API rollout. Worker startup validates SMTP configuration and,
when SMTP_VALIDATE_ON_STARTUP=true, its connection. Beat remains opt-in: update it
with `make docker-celery-up` when changing schedules. Keep API/worker images
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
  known transient domain failures. Mail implements bounded delivery retries and
  a Redis failure archive as described below.
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

## Authentication mail

AuthService calls `core/mail/queue.py` asynchronously. `b4fastapi.mail.send` runs
`MailService` in a standalone worker; the API no longer starts a BRPOP consumer.
EMAIL_ENABLED=false skips both publication and consumption. Existing
EMAIL_QUEUE_MAX_RETRIES (default 3) and EMAIL_QUEUE_RETRY_DELAY_SECONDS (default 2)
mean one initial SMTP attempt plus up to three delayed retries. Delays release the
worker instead of sleeping inside its processing loop. EMAIL_QUEUE_BLOCK_TIMEOUT_SECONDS
was removed; old local values can be removed during env synchronization.

Every job carries creation/expiry timestamps based on the corresponding token TTL.
Expired or malformed messages are archived without SMTP delivery. Tokens remain
validated by the API; this expiry check is an additional stale-mail guard. Reissuing
or consuming a token may invalidate a queued link earlier than its TTL.

Terminal failures go to the Redis hash `<CELERY_KEY_PREFIX>mail:failures` in the
Celery broker, keyed by task ID. Records include original message, trace ID, reason,
attempt and failure time. Repeated writes overwrite the same entry. No raw SMTP
error text or token link is logged. The task completes after archiving, so Celery
SUCCESS means processing finished, not necessarily that SMTP delivery succeeded.

If archival fails, a 60-second retry carries failure_reason and only retries
archival, without another SMTP attempt. These storage retries are unbounded until
Redis recovers. If the replacement message itself cannot be published, or a worker
is killed before acknowledgment, the original delivery can be redelivered and may
repeat SMTP. SMTP does not provide exactly-once delivery. Monitor retry logs,
worker availability and failure archive growth; persistent process crashes also
need operator intervention.

The failure archive contains recipient data and secret links: restrict Redis
access and define operational retention/cleanup. It has no automatic expiry or
public API. Inspect its count using HLEN and retrieve individual records only in a
secure operator session. Do not blindly replay archived authentication messages;
request a fresh verification/reset link instead. Redis persistence, backups and
no-eviction policy determine archive durability. No SQL migration is required.

## Upgrade from the legacy mail queue

1. Pause new signup/resend/reset requests or put the service in maintenance mode.
2. Keep the old API/worker running until `queue:mail:jobs` is empty and in-flight
   sends/retries have completed; queue length alone is not proof of completion.
3. Securely inspect/back up `queue:mail:dlq`; it is left untouched by this release.
   Resolve failures by requesting fresh links after rollout, not by copying these
   envelopes into the Celery queue. Do not flush shared Redis.
4. Deploy the new image/config and standalone worker, then the API. Docker startup
   now waits for the worker when mail is enabled. For manual deployment use inspect
   ping and a test mailbox before reopening requests.
5. Monitor delivery and the new failure archive. If rolling back, stop new
   publications and drain Celery first; old APIs cannot consume Celery messages.

No automatic legacy import is performed. For users who have not enabled email or
have no pending messages, there is no backlog to migrate. Never run old producers
while assuming the new worker will consume their list envelopes.

## Background work audit after migration

| Work | Owner | Decision |
| --- | --- | --- |
| Signup verification / password reset | Celery -> MailService | Migrated; async producer API preserved. |
| Retry / terminal failure handling | Celery countdown / Redis failure hash | Replaces BRPOP, blocking retry sleep and old list DLQ. |
| Worker start / stop | Process manager or Docker | Removed legacy task_queue worker/bootstrap from API lifespan. |
| SMTP `asyncio.to_thread` | Existing MailService inside Celery task | Retained as an execution helper. |
| SSE heartbeat / Redis subscriptions | FastAPI request lifecycle | Retained; connection-bound streaming and cancellation are not queue tasks. |
| DB migrations, API SMTP validation, readiness | API startup / deployment | Retained; service readiness depends on completion. |

Lifecycle notifications use a one-minute durable outbox scan; the earlier auth-mail task remains independently queued.

References: [Celery Redis delivery caveats](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html),
[periodic tasks](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html).


Subscription-start, plan-change and account-deleted mail use migration 0011 encrypted outbox. Deletion notice commits with deletion. One Celery Beat scans every minute; existing auth/welcome mail policy remains unchanged. See [billing setup](../../notes/billing.md) for webhook activation, retention, key rotation and duplicate-delivery limitations.

Billing reconciliation (b4fastapi.billing.reconcile) runs every 300 seconds, reads at most 50 stale customer snapshots and refreshes them from Stripe. Apply migrations 0012–0013 first. One Beat plus workers is required; no frontend polling is used.
