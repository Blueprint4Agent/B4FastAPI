# Commit Title

feat(logging): unify compact console log formatting

# Changed File Scope

Backend console logging and lifecycle warning routing, access/application log tests, English/Korean lifecycle
logging documentation and this worklog. Follow-up in the existing lifecycle PR.

# Reason

Default Uvicorn client ports, HTTP versions and successful preflight messages obscure
actual requests. Show time, method, full path/query and status in a compact console line.
Align INFO/WARNING/DEBUG/ERROR/CRITICAL with the same timestamp/column style.

# Design

Format only console access handlers; preserve original records for OTLP/file handlers.
Hide only successful 2xx OPTIONS on console, retaining failed preflight and all actual
requests. Keep the existing exact /metrics exclusion. Preserve query strings without
truncation. Keep error tracebacks, request/trace/task IDs and DEBUG source context. Respect
NO_COLOR and the actual handler stream. Preserve caller file formatters. No request
execution, auth, CORS, sampling or response changes.

# Verification Plan

Run root make verify-plan and make verify. Exercise mixed GET/OPTIONS status records,
handler idempotency, original-record preservation and isolated real Uvicorn HTTP smoke.

# Impact

Console presentation changes only. No dependency, schema, API or frontend changes.

# Loop Alignment

Request execution still follows the existing router/service/data/error loop; only the
console sink changes. Domain-event, background-task and frontend loops are not
applicable because no events, tasks or UI behavior change.

# Verification

- Root `make verify-plan` selected backend runtime checks and documentation checks;
  `make verify` passed architecture, environment contract, Ruff, 387 backend tests
  and OpenAPI contracts. No selected check was omitted.
- Frontend runtime/browser/build checks were not selected for this follow-up because
  no frontend content changed; the first commit's full frontend/integration checks
  remain valid and branch-wide pre-push verification checks receipt applicability.
- Real isolated Uvicorn GET/OPTIONS smoke passed: only failed preflight appeared on
  console, all five standard levels were aligned, exception traceback remained and
  successful cleanup ended with Bye!!. Redirected output had no ANSI sequences.
- Regression tests preserve original file messages/formatters and request arguments,
  DEBUG source/correlation context, error IDs/tracebacks and idempotent filters.
- The passing backend run reported Pydantic/argon2/auth deprecations and asyncpg
  cancellation-coroutine RuntimeWarnings. These warnings are recorded without
  changing unrelated model/database-test behavior in this logging follow-up.
