# Commit Title

feat(backend): add branded lifecycle status panels

# Changed File Scope

Backend lifespan, observability startup presentation, settings, dependency lock,
startup/shutdown regression tests, Docker env example, English/Korean documentation,
and a frontend pin integrating a documentation-only formatting repair needed by the
existing full verification gate.

# Reason

Replace repetitive startup console messages with an English B4A panel that separates
service role, configured stack, enablement and actual verification evidence.

# Design

Keep sequential startup and fail-closed initialization. A startup-scoped reporter
renders Rich Live on interactive terminals and static panels in Docker/redirected
output. Explicit plain mode emits durable lines.
Only console startup INFO duplication is filtered; OTLP records and warnings/errors
remain. Disabled/configured/verified/failed/not-run are distinct. No secrets or unverified Celery health claims. Cache now performs a bounded
five-second Redis PING and fails startup on failure. Failed/cancelled new Redis
clients close before publication; startup failures release acquired resources.
The header shows APP_MODE and LOGIN_ENABLED, including bootstrap mode. Storage cleanup remains lifespan-owned. A matching cleanup table reports actual
Database/Redis/Storage closure; Bye!! follows successful normal cleanup only.
Redis cleanup is attempted even when database disposal fails.

# Verification Plan

Run make verify-plan then make verify, plus isolated terminal/plain startup previews
and failure/cancellation/log-routing tests. Check actual PR metadata before completion.

# Impact

Adds Rich and STARTUP_DISPLAY=auto|plain|off. No API/schema or frontend runtime changes. Cache availability becomes a startup
requirement through a bounded PING before OAuth/email/billing/DB initialization.
Existing service ordering remains; startup failure cleanup now covers DB/Redis too.

# Loop Alignment

Request, domain event and background task loops are not applicable: this changes
process lifecycle presentation and startup dependency verification only. Existing initialization and shutdown stay owned
by the app lifespan. Frontend loops are not applicable because the child change only formats Markdown.
The documentation-only child PR #66 was merged before updating the parent pin.

# Verification

- `make verify-plan` selected backend plus full frontend/integration checks because
  runtime configuration and dependencies changed. `make verify` passed all selected
  checks; no selected checks were omitted.
- Backend: 383 tests passed, including 31 lifecycle display/probe/cleanup regressions;
  architecture, Ruff, env contracts and OpenAPI checks passed.
- Frontend: static checks, 147 unit tests, 169 browser UI tests, production route and
  style-studio suites passed. Parent contracts, packaging and custom-brand build
  checks passed. No frontend runtime source was changed.
- Isolated real Uvicorn smoke passed with temporary SQLite migrations/local storage,
  FakeRedis PING and HTTP `/ping`; interactive PTY, Docker-style redirected static
  panels and explicit plain output were checked. Redirected output contained no
  ANSI cursor sequences. Normal cleanup completed before Bye!!.
- Failure/cancellation, disabled/configured states, failed/unreached services,
  runtime/login metadata, log-handler preservation and failed cleanup without
  farewell have regression coverage. Live SMTP/Stripe/production data operations
  were not needed; integration boundaries are mocked and smoke data is temporary.
- Initial verification exposed existing child worklog Prettier drift. B4React PR
  #66 repaired only Markdown formatting, passed its documentation scope and was
  merged as d4878ea before this parent gitlink update. The full parent harness then
  passed without skipping that gate.
