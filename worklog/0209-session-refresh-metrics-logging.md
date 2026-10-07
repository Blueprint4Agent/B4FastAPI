# Commit Title

feat(billing): persist subscription state and synchronize lifecycle updates

# Changed File Scope

Frontend submodule, backend subscription persistence/reconciliation, observability logging, root db-current/db-migrate targets and regression tests, localized documentation.

# Reason

Avoid redundant authentication and subscription requests and remove routine metrics scraping from access logs.

# Design

Scope expanded by user: persist per-customer/mode subscription snapshots, update after verified checkout/mutations and signed webhooks, serialize provider reads with customer locks, and reconcile stale snapshots in bounded Beat batches. GET reads DB; missing legacy snapshots bootstrap once. Webhook delivery retries on sync failure; provider current state wins over event order.

Integrate child shared recovery transport and event-driven subscription reads. Filter exact /metrics access records on uvicorn.access without changing endpoint behavior or application error logging.

# Verification Plan

Run make verify-plan and make verify. Test metrics path/query filtering and preservation of unrelated paths and diagnostic logs.

# Impact

Bootstrap /config now mints a fresh short-lived credential instead of reusing a startup token. Additive migrations 0012–0013; no API schema change. Metrics access logs are suppressed; collection and diagnostic logging remain.

# Loop Alignment

Backend request/service/model loop persists snapshots under customer locks. Signed webhook events synchronize current provider state independently of email; bounded Celery reconciliation repairs missed events. Frontend identity recovery remains AuthProvider-owned and subscription snapshots are shared by an account-scoped provider. No new SSE stream is added: explicit reload/new sessions read webhook-updated DB state; known local mutations update consumers immediately.

# Verification

Root make verify-plan selected backend=True/frontend=full; make verify passed 280 backend tests, 140 frontend unit/integration tests, 164 UI tests, 9 production-route tests, 3 style-studio tests, hooks/architecture/lint/types, contracts and packaging. All selected checks ran; live Stripe/SMTP delivery, production deployment and native installers are outside scope. Snapshot read/mutation/webhook/reconciliation and bootstrap expiry/metrics regressions passed. Final merged child pin is recorded below.

Child PR Blueprint4Agent/B4React#60 merged with merge commit ca3f83f8f351824bda59743fae2c5004b1291e38; child pre-push full verification passed. Local make db-migrate applied 0013_subscription_identity and make db-current confirmed head. Migrations remain sequential because 0012 had already been applied locally.

Final verification after the merged child pin and split migration chain: make verify-plan / make verify passed the full selected scope, including backend/frontend tests, production routes, style studio, contracts, packaging and project build. No selected checks were omitted.
