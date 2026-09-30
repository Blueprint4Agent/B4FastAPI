# Commit Title

feat(billing): verify Stripe configuration and connectivity at startup

# Changed File Scope

Billing service, API lifespan, isolated startup tests/test fixtures and English/Korean
billing/backend documentation, a bearer/API-key/admin policy audit and regression
tests. Continue the existing named billing branch and PR #77.

# Reason

When STRIPE_ENABLED=true, detect misconfiguration and failed Stripe authentication or
connectivity before the API accepts traffic, matching the SMTP startup failure policy.
Also inventory other API-key restrictions requested by the user and verify that
Swagger security declarations match the current auth guards, without changing permissions.

# Design

Lifespan awaits BillingService.initialize after mail validation and before migrations.
Disabled Stripe skips all checks and network I/O. Enabled Stripe validates secret key
and trusted return URLs, then uses the actual async SDK to read one Checkout session.
Reuse bounded provider requests, close clients, sanitize failures and abort startup.
No remote customers, Checkout sessions or charges are created; no schema/API change.
The probe establishes key authentication and Checkout read permission, not Link
eligibility, write permission, live activation or end-to-end card registration.

# Verification Plan

Root make verify-plan then make verify against the full branch base. Use real SDK with
mocked HTTP transport for success/auth/permission/network/timeout cases; assert lifespan
failure prevents migrations and startup completion. Preserve hermetic general tests
independently of developer Stripe credentials. Add actual issued-key tests for six
session-only endpoints, regular/admin roles and API-key-accepted workflows. Validate
commit and actual PR metadata.

# Impact

Stripe-enabled deployments now fail startup on invalid config or failed probe; disabled
deployments make no Stripe calls. Probe runs per API worker start with bounded retries.
No frontend, migration, contract, SMTP or worker behavior changes.

# Loop Alignment

Startup validation must finish before serving HTTP. Request lifecycle stays unchanged.
Domain events and background tasks are not applicable to a blocking read-only startup
probe; no state projection or asynchronous UI refresh is introduced.

# Verification

VERIFY_BASE=adcadab make verify-plan selected backend and full frontend for the whole
billing branch. Root make verify passed all selected checks: hook fixtures, project-init,
architecture/env/lint/contracts, 191 backend tests, 102 frontend tests, 71 UI tests,
6 production route tests, 3 style-studio tests, integration packaging and build fixtures.
No selected checks omitted. Frontend code and permissions were not changed.

20 startup tests cover disabled bypass, local field errors, test/restricted/live keys,
actual SDK GET serialization, auth/permission/API/network/timeout failures, client closure,
sanitized traceback and application startup/migration ordering. Ten auth-audit tests use
real issued keys on isolated SQLite: all six bearer-only operations reject keys, the two
admin operations require current owner role, regular operations accept keys, stale bearer
cannot be bypassed with a key, and the OpenAPI session-only inventory matches runtime.

A separate read-only probe using the configured local Stripe credentials passed. No
customers, sessions, payments or other remote resources were created. This verifies the
probe itself, not actual card registration, Link eligibility or every write permission.
PostgreSQL execution and end-to-end card registration remain untested for this change.

The first complete run hit an existing SettingsPage deletion-code input wait failure.
The debug-live test launch did not stop at its breakpoint; the breakpoint was cleared.
The unchanged full 102-test frontend suite then passed, as did final root verification.
No frontend source was modified and the original intermittent cause was not established.

Startup is a blocking read-only lifecycle check; domain events/background tasks and new
frontend loops are not applicable. Existing request authentication policy is unchanged.
