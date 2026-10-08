# Startup and shutdown display

The API defaults to `STARTUP_DISPLAY=auto`. Interactive terminals at least 76
columns wide show a cyan B4A banner, service icons and a live status panel.
The header identifies Mode: Development/Production from APP_MODE and Login:
Enabled/Disabled from LOGIN_ENABLED. Disabled login adds Bootstrap session;
APP_ENV is a telemetry label and does not determine the runtime mode.

```text
SERVICE     STACK             ENABLED  CHECK
Storage     Local             Yes      ✓ Verified
Cache       Redis             Yes      ✓ Verified
OAuth       Google · GitHub   Yes      ✓ Configured
Email       Gmail SMTP        Yes      ✓ Verified
Billing     Stripe · Test     No       — Not checked
Database    PostgreSQL        Yes      ✓ Ready
```

This is an example, not a claim about your environment. Stack names are derived
from settings: Local/Amazon S3/Cloudflare R2/Supabase; configured OAuth providers;
Gmail SMTP for smtp.gmail.com, SMTP otherwise; Stripe Test/Live; PostgreSQL/SQLite.
Storage and database are required. A configured stack is not proof of connectivity.

Checks update in place from Pending to Checking… and then Verified/Configured/Ready.
Database additionally displays Migrating… and Initializing…. OAuth validates only
configuration. When SMTP_VALIDATE_ON_STARTUP=false, Email displays Configured with
Connection check skipped. Disabled integrations display No / Not checked. Failed
checks display Failed and abort startup; later enabled services become Not run.
The panel only exposes exception types; existing error diagnostics stay available.

On normal server shutdown a matching panel displays Database, Cache and Storage
changing from Pending to Closing… to Closed. Cache identifies Redis or Redis ·
In-memory; an unopened lazy client is Not opened. This describes this API process's
client cleanup, not stopping the Redis server, database server or Celery workers.
All cleanup must succeed before `B4A · Bye!!` appears. Startup failure, failed
cleanup and forced termination do not produce a successful farewell. A DB cleanup
failure still attempts Redis and storage cleanup.

| Setting | Behavior |
| --- | --- |
| `STARTUP_DISPLAY=auto` | Animate capable terminals; preserve static panels in redirected/container logs |
| `STARTUP_DISPLAY=plain` | Durable line-oriented lifecycle records |
| `STARTUP_DISPLAY=off` | Original service/Uvicorn lifecycle logging |
| `NO_COLOR=1` | Disable colors; terminal animation remains available |
| `LOG_LEVEL=WARNING` or higher | No INFO-level panels or farewell |

Redirected/container output retains the banner and final startup/shutdown panels
without cursor animation. Select plain explicitly for line-oriented log ingestion.
Dumb/narrow terminals and recognized `--workers`,
`WEB_CONCURRENCY` or `UVICORN_WORKERS` counts above one use plain output. For
programmatic multi-worker Uvicorn configuration, set STARTUP_DISPLAY=plain.
Reload supervisor logs remain visible; each replacement process displays its own
startup/cleanup. Native Uvicorn serving-address/access/error logs are preserved.

Only console duplicates are filtered. Original startup records remain available
to OTLP and file handlers; warnings/errors are displayed above the live panel.
No connection strings, passwords or provider responses are added to panels.
Cache performs a Redis PING with a five-second startup timeout before OAuth/mail/
billing/database initialization. A failed probe aborts startup and closes acquired
clients. Redis · In-memory identifies the FakeRedis development backend. Shutdown
closes the client initialized at startup. Celery workers are not claimed healthy
without an actual worker probe.

Korean: [시작 및 종료 화면](ko/startup-display.md).
