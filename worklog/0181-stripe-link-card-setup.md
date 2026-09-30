# Commit Title

feat(billing): add Stripe and Link card setup foundation

# Changed File Scope

Backend billing settings, Stripe SDK/lock, models/migration, services/router, tests,
OpenAPI baseline, environment examples, English/Korean setup documentation and
the coordinated B4React gitlink (contract + API/error/hook adapters).

# Reason

Introduce authenticated, charge-free card and Link registration as the first payment integration.

# Design

Bearer session -> billing router -> service -> customer repository / async Stripe SDK.
Persist a per-user customer mapping and stable UUID for customer creation retries.
Use Stripe-hosted Checkout in setup mode with card and Link; only server-configured
return URLs. Read completion from Stripe with customer ownership validation and
expose only safe payment-method summaries. Stripe remains the source of truth:
no local payment state, charges, subscriptions or unauthenticated callback claims.
Additive contract coordinated with a B4React PR for generated types and billing API/error/hook adapters; update its gitlink only after the child merge.

# Verification Plan

Run root make verify-plan and make verify; add API auth/validation contracts, service
ownership/provider failure tests, SQLite migration/customer uniqueness integration.
Export OpenAPI and confirm pinned frontend compatibility. Validate staged governance,
commit body, ready PR metadata and installed hooks. Live Stripe smoke requires a
sandbox secret key and will be recorded separately from mocked validation.

# Impact

Disabled by default; operators configure a test secret and trusted return URLs.
Additive database table with user cascade; remote Stripe customer data is retained
on local account deletion and requires operator retention handling. No real charges. Stripe cursor pagination exposes has_more/next_cursor without
inventing an offset total; it follows the external provider collection contract.

# Loop Alignment

Request lifecycle follows router/service/repository/domain errors. Domain event and
background task loops are not applicable: setup URL creation is required immediately,
and authoritative registration state is fetched from Stripe on request. No local
payment projection or frontend subscriber is introduced. Webhook-driven billing and
frontend refresh/composition/connectivity are deferred with their owning features.

# Verification

make verify-plan selected backend plus full frontend scope (dependency/config/API and
contract changes). make verify passed all selected checks: Git-hook fixtures,
project-init checks/tests, backend architecture/lint/environment contract, all 161
backend tests, matching provider/consumer OpenAPI, frontend check/test (102 tests),
UI (71), production routes (6), style studio (3), packaging and project-build fixtures.
Unchanged child checks reused valid content-bound receipts where available; parent
production routes, contracts and packaging ran locally. No selected check was omitted.
42 billing tests cover bearer isolation, validation, sanitized errors, Stripe ownership,
SetupIntent confirmation, safe card/Link summaries, stable retry keys, concurrent
SQLite reservations, mode separation, seeded existing accounts and deletion cascade.
Environment sync preserved existing local values and created recoverable backups.
Live Stripe registration and PostgreSQL execution were not run: no sandbox key or
isolated PostgreSQL service was configured. SQLite migration/application flows passed;
this is not evidence of a live Stripe account, Link eligibility or actual card registration.

B4React PR #34 merged with merge commit d06ebaa72b9c90fb79a11172291f567611bf10ff;
its authored commit is c86ba0d. Parent pins that merged revision. Child staged and
actual PR governance and pre-push full-range checks passed without bypassing hooks.

Final SDK protocol regression uses the actual installed StripeClient and replaces only
its HTTP transport. It verifies setup serialization, the Idempotency-Key header,
SetupIntent expansion and customers.payment_methods.list_async. This caught and fixed
a mock-only customer payment-method service-path mismatch before committing. Final
root verification after that correction passed 161 backend tests (42 billing).
