# Commit Title

refactor(config): unify billing under the Stripe switch

# Changed File Scope

Billing settings/services, public/admin contracts, environment examples, frontend gates, tests and docs.

# Reason

Use STRIPE_ENABLED as the sole payment/subscription switch and remove the separate subscription option.

# Design

Remove duplicate configuration and contract fields; all billing and plan paths use billing_enabled. Enabled startup validates configured subscription prices. Remove duplicate admin row.

# Verification Plan

Run root make verify-plan and make verify, enabled startup/disabled requests and admin UI regressions.

# Impact

Stripe true requires complete plan configuration. Stripe false disables all billing. Existing subscriptions are not cancelled.

# Loop Alignment

Existing request/error and frontend recovery/owner loops retained. No new background or domain event operation.

# Verification

make verify-plan / make verify selected backend=True, frontend=full and passed: 268 backend tests, 130 Vitest tests, 155 UI browser tests, 9 production-route tests and 3 Style Studio tests. Hooks, architecture, environment/ API contracts, lint, format, typecheck, policy checks, packaging and project build passed. No checks skipped. Local backend/docker env files had only the obsolete switch/comment removed; secret values were not changed.

B4React PR #58 merged first with merge commit 8dc01ddad191334dbe06854aa5ab4e0313d0f48e. Actual PR governance and child pre-push full verification passed. Parent integrates the identical verified source and rechecks contract/package output; no business event/background loop was added.
