# Commit Title

feat(billing): connect Stripe subscription checkout

# Changed File Scope

Backend billing schemas/service/router, reservation migration, configuration/contracts, tests/docs and frontend gitlink.

# Reason

Plan selection currently has illustrative prices and no subscription checkout; connect it to server-owned Stripe prices and verified subscription state.

# Design

Read Stripe recurring prices from a server allowlist. Create hosted subscription Checkout for the authenticated customer with durable per-customer reservations and provider idempotency. Verify ownership and subscription/payment state on return; read current subscription from Stripe rather than trusting the URL. Keep saved-card registration in Settings. Sandbox catalog uses the previously selected example amounts. Account deletion with checkout history is blocked for operator review under the existing user transaction lock, so deleting a local account cannot silently orphan recurring billing. No local entitlement grants or webhook projection in this initial integration; authoritative reads refresh on return/focus/recovery.

# Verification Plan

Provider-mocked API/domain/integration tests for price validation, ownership, duplicate requests and pending/failed returns; frontend state/navigation and family comparisons; Make verify-plan/verify, sandbox configuration read checks and hosted checkout smoke without submitting a payment.

# Impact

Monthly/annual cards open hosted checkout when server pricing is configured. Disabled/unconfigured states remain explicit. No automatic live charges or purchases during verification.

# Loop Alignment

Router/service/repository lifecycle, typed frontend domain hook, existing recovery loops and shared settings/plans composition. Stripe read-through status needs no asynchronous local projection; no webhook event/worker claims or paid entitlement enforcement.

# State Ownership

Server owns price allowlist and customer/checkout reservations. Stripe owns subscription truth; frontend owns only pending actions and snapshots.

# Memoization

Three small cards and modest settings sections need no extra memo boundaries; stabilize API hook and ignore stale account requests.

# Performance Evidence

Verify request counts and stale responses with tests; no latency claim.

# Verification

- `VERIFY_BASE=7cd0a83 make verify-plan` selected backend and full frontend verification for 26 changed files; `make verify` passed all selected checks including hooks, architecture, environment/contracts, packaging and project build.
- Backend 209 tests; frontend 115 tests, 80 browser UI cases, 7 production route cases and 3 style studio cases passed. Browser cases preserve the settings page family across mobile/desktop and light/dark themes; hook tests cover stale account responses and duplicate actions.
- B4React PR #40 merged with merge commit `ddca08920682beb07b0a300599a81f700b85c6c4`; parent validates the pinned consumer contract and packaging.
- Actual Stripe test-mode startup/catalog validation passed for all four configured recurring prices. An isolated temporary database smoke created card/Link setup and subscription Checkout sessions, reused the subscription attempt, verified owner status and hosted HTTP 200, then expired sessions and removed the smoke customer. No application database data or actual payment was used.
- No selected checks omitted. Payment submission/settlement, native client return and deployment were not exercised. Domain-event/background loops are not applicable because subscription truth is read from Stripe without a local entitlement projection; API state, recovery and UI composition loops are covered.
