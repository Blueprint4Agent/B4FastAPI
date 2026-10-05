# Commit Title

feat(billing): manage billing details and cards in app

# Frontend Integration

B4React PR #46 merged with merge commit `92b3ca2ae8f8ce4fd097094d9db07263df4f6bc4`; parent pins this verified child. Actual child PR metadata and local pre-push checks passed.

# Changed File Scope

Billing API/models/service/config, contracts, tests, bilingual docs and frontend integration.

# Reason

Edit billing profile inside the app, display real saved cards with direct management, remove the permanent refresh control and avoid portal redirects for profile/card actions.

# Design

Owner-scoped profile updates with structured address. Owner-checked default/detach card actions serialized on the customer row, disallow removal of an active subscription default. Embedded Stripe Payment Element uses card-only SetupIntents and optional mode-matched publishable key; no PAN/CVC enters application APIs. Verify SetupIntent owner/status after confirmation. Preserve separate Link wallet identity when provider does not return underlying card fields. Existing hosted subscriptions/portal invoices remain. Shared compact DropdownMenu handles icon/danger items, floating content-width placement and viewport recovery, with a searchable showcase; no billing-specific menu styling.

# Verification Plan

Ownership, validation, update/default/delete/setup tests; frontend modal and API recovery tests; desktop/mobile browser comparison; Make-selected full verification and contracts.

# Impact

New authenticated APIs and optional publishable-key configuration; no migration or charging behavior change. Existing hosted setup API retained for compatibility.

# Loop Alignment

Router/service/model/provider ownership path retained. Stripe owns setup authentication and storage; no local worker/event needed. Frontend hooks own snapshots/actions with owner-generation guards and focus/online recovery. Shared modal/input/button/feedback controls used.

# Verification

`make verify-plan` selected backend + full frontend for API/contract/dependency/runtime changes. `make verify` passed: hooks, init/build isolation, backend architecture/env/lint and 227 backend tests; 119 frontend tests; 102 UI cases; production route recovery, style studio, contract/package checks. No selected checks omitted. Native desktop bundling is not applicable to browser billing UI. Synthetic Stripe test customer: public/secret key account match, SetupIntent success, saved Visa 4242 details, default and detach verified; no charge created and customer deleted. Read-only inspection of the screenshot invoice showed one Link method, no card fields and no additional page. Worklog-only outcome edits retain runtime evidence; text/governance are revalidated before push.
