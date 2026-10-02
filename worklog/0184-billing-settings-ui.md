# Commit Title

feat(frontend): integrate billing settings and plan selection

# Changed File Scope

Parent scope: src/frontend gitlink, notes/billing.md, notes/ko/billing.md and this worklog. B4React PR #36 owns pages, navigation, billing hook, styling, translations and tests.

# Reason

Expose the existing Stripe card/Link registration flow and introduce Free, monthly and annual plan selection using the supplied layout references.

# Design

Settings owns a billing page and page-owned domain hook over existing typed API adapters. A lazy plans route offers three options and links paid selections to card registration. Example template prices: Free, monthly KRW 3,990 / USD 3.99, annual KRW 39,900 / USD 39.99. Currency is a display-only URL preference, not FX conversion. No subscription, invoice, cancellation or entitlement API exists; present these as unavailable rather than fabricate paid state. Reuse shared buttons/cards/messages. Verify hosted return parameters with the provider-backed status endpoint. Owner changes and unmount invalidate pending work; desktop recovery and browser focus/online refresh data. Deduplicate actions and retain a retry UUID within the active owner session.

# Verification Plan

Focused hook/page integration tests for loading, provider errors, disabled state, ownership, retry and return handling; browser mobile/desktop light/dark navigation and registration flow. Run make verify-plan and make verify, governance and PR checks. Parent validates pinned contracts and packaging after child merge.

# Impact

New billing settings entry and profile plan link; no backend schema/API changes or real charges. Template prices are not live Stripe prices. Actual subscriptions remain pending operator configuration and backend implementation.

# Loop Alignment

API page/hook/adapter loop retained. No billing realtime events exist; refetch on return/focus/online and desktop recovery. UI composition reuses existing shared primitives and app.css. No new worker/domain event loop for frontend-only registration.

# Verification

Child PR #36 merged as b4750abd014d102b4ce8ec694c47185393c460e7 (authored commit 3844705). Child full verification passed: 110 Vitest tests, 78 UI scenarios, 7 production route/branding checks and 3 style studio checks. Mobile/desktop English/Korean screenshots inspected, including final action buttons. Root full-branch VERIFY_BASE=8d5e2f7 make verify-plan and make verify passed with backend=True, frontend=full. Observed 189 backend tests, 110 frontend tests, 78 UI scenarios, 7 production route/branding tests, 3 style studio tests, hook/project-init/architecture/env/contract checks, packaging and project-build fixtures. No selected checks omitted. No real Stripe writes, live charges or native external-browser recovery tests: provider flows use mocked isolated responses and subscriptions are intentionally unavailable.
