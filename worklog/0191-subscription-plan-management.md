# Commit Title

feat(billing): schedule subscription plan changes

# Changed File Scope

Backend billing schema/service/router, contracts, tests, bilingual docs and frontend gitlink.

# Reason

Paid users need to switch to Free or change monthly/annual billing and undo a pending change.

# Design

Apply all changes at the current paid period end, without immediate charges or refunds. Stripe subscription schedules own future paid-plan changes; cancel_at_period_end owns Free transitions. Confirm effective date before submission, retain current plan until transition, show pending target and allow undo. Serialize owner mutations and reject stale confirmations; provider remains the source of truth. Unknown/provider-managed schedules are not overwritten.

The requested settings reference also adds real recent invoices, customer billing profile and a restricted Stripe portal for profile/card management. Retain the shared Settings family rather than copying screenshot colors; show actual provider defaults and no invented payment methods.

# Verification Plan

Owner/auth/stale request tests, provider schedule lifecycle and cancellation/undo, frontend confirmation and refreshed state, root Make verification and isolated Stripe sandbox smoke.

# Impact

Self-service plan changes become available for supported active single-item subscriptions. No entitlement/webhook projection or immediate refund behavior is added.

# Loop Alignment

API lifecycle follows router/service/repository; provider owns scheduled execution, so no local domain worker/event is needed. Frontend API snapshots/recovery and shared Modal/Button/toast composition remain in existing loops.

# State Ownership

Stripe owns current/pending subscription state; server validates target prices and stale versions. Hook owns snapshots/mutations; page owns confirmation selection. No new store.

# Memoization

No expensive repeated boundary introduced; three plan cards and a single controlled dialog do not justify memo wrappers.

# Performance Evidence

Mutation locking, stale account handling and browser confirmation checks passed in the child and root suites; no latency claim.

# Verification

VERIFY_BASE=738e6cf make verify-plan and make verify passed: backend=True, frontend=full, 20 classified files. Passed 218 backend tests, 116 frontend tests, 89 browser scenarios, production route checks and 3 style studio cases, plus hooks, initialization, architecture, environment/contracts, frontend packaging and project build checks. No selected checks omitted. Child PR #43 merged as f8ac808a4bbd71c5fc656bc09d72222de3455028 before parent integration.

An isolated actual Stripe sandbox test verified monthly-to-annual scheduling without an immediate charge, cancellation/undo, actual annual renewal through a test clock, annual-to-monthly scheduling, profile/default card/invoices and restricted portal creation. Synthetic customer/subscription/test clock were removed; application data untouched and no live charges. Portal-inclusive startup verification passed. Live deployment and native desktop runtime were not exercised; Stripe owns scheduled execution, so no new local worker, SSE or webhook projection loop was added.

# Page Family

## Family

Standalone plans, Settings and shared confirmation modal.

## Reference

Existing PlansPage, BillingSettingsPage and shared Modal/ModalButton.

## Shared Rules

Reuse existing page shells, settings rows, modal focus/scroll/actions and toast feedback.

## Exceptions

No new styling exceptions. Pending subscription details are domain content within existing rows.

## Evidence

Child worklog 0050 records Settings peer comparisons and plan-change journeys. Existing mobile/desktop light/dark geometry checks passed. Screenshots at /tmp/b4-managed-billing-ui/billing-paid-subscription--4601b-d-billing-details-at-1440px/billing-details.png and /tmp/b4-managed-billing-ui/billing-paid-subscription--fbee7-nd-billing-details-at-390px/billing-details.png were visually reviewed: grouped sections, compact actions and mobile invoice rows without overflow.
