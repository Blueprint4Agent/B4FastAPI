# Commit Title

fix(billing): preserve verified subscription identity and mode

# Changed File Scope

Backend billing service, billing regression tests and fixtures; English/Korean billing audit and guides. Frontend pinned sources are reviewed and tested without edits.

# Reason

Issue #93 requires reproducible checks of payment ownership, replay/recovery, catalog currency, management timing and notification boundaries before #95.

# Design

Keep router/service/provider layering and existing customer locks, snapshots and signed webhook synchronization. Preserve subscription identity during immediate upgrades; verify expanded provider object mode when confirming Checkout; represent multiple subscriptions as existing but unknown. No API shape or DB migration change. Audit existing card/Link, profile, invoices and frontend state/retry flows; document unresolved operational work separately.

# Verification Plan

Reproduce defects with DB-backed regression tests, then root make backend-test and frontend delegated billing hook/browser tests. Run make verify-plan then make verify for complete branch scope. Inspect official Stripe event/receipt guidance; use read-only sandbox validation if configured and never create charges or refunds.

# Impact

Fixes internal subscription identity loss and fail-closed payment confirmation. Ambiguous subscriptions cannot appear purchasable. No payment provider or frontend source changes.

# Loop Alignment

Request lifecycle preserved through BillingService. Domain synchronization stays in signed webhook and reconciliation paths; no new realtime event because existing frontend explicitly reloads shared DB snapshots. Background Beat reconciliation unchanged. Frontend API state, desktop recovery and shared composition reviewed; no new UI or polling.

# Verification

- Before fix: six new assertions failed (mode mismatch/missing, multiple subscriptions, upgrade identity).
- Focused billing/backend: 91 passed; frontend billing hook/API/component: 31 passed; browser billing: 52 passed.
- make backend-format, make verify-plan then make verify passed (40.3s); scope backend=True/frontend=docs. Selected project init fixtures, architecture, environment contract, Ruff, full backend suite (396 passed) and OpenAPI contract checks.
- Frontend broad rebuild/route suite omitted by classifier: no frontend source/pin or API shape changes; targeted billing unit/browser audit was run separately.
- Read-only configured Stripe test startup/catalog/portal validation passed; eight prices verified. No customer/session/payment/refund/email created. Webhook secret unset; external delivery and hosted checkout remain pre-production checks documented in both audit locales.
- No new realtime/UI loop: existing shared snapshot and explicit refresh policy retained. No migration required.
- git diff --check passed. Planned and actual PR governance required before merge.
