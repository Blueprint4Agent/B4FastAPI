# Commit Title

feat(billing): add invoice history and lifecycle notifications

# Changed File Scope

Additional frontend scope: keyboard shortcuts and local persistence, compact shared controls/showcase, settings entry animations, home/admin headers, profile role placement and subscription glyph geometry.

Billing invoice paging/detail and lifecycle recovery, notification outbox/webhooks/mail, account deletion, frontend history/retry UI, settings animation, contracts/tests/docs.

# Reason

Keep billing history inside the app, isolate section failures, recover partial subscription changes, and send only subscription-start/plan-change/account-deleted emails. Replay settings entry animation per sidebar section.

# Design

Use owned invoice APIs and shared Modal/Tooltip. Independent billing section snapshots/retries. Signed Stripe events plus encrypted durable outbox and existing Celery/SMTP path; deletion notification saved in deletion transaction. Subscription schedule retry verifies the original snapshot and matching provider idempotent creation response before recovery. No failure or renewal emails.

# Verification Plan

Run root verify-plan/verify; regression tests for ownership/cursors, partial failures/idempotency, signed/deduplicated events, deletion atomicity, worker retries and UI dialog/retry/animation behavior.

# Impact

New additive outbox migration and optional webhook secret; webhook configuration and Celery Beat required for durable notification delivery. No real charges or external emails in tests.

# Loop Alignment

Request/service/repository/error loop; durable mail event outbox consumed by bounded background workers. Frontend account-owner/recovery guards remain. No realtime entitlement projection added.

# Verification

Root make verify-plan selected backend=True/frontend=full. make verify passed hooks, project identity/build tests, backend architecture/lint/format, environment contract, 274 backend tests, provider/consumer contracts, frontend architecture/format/types, 131 unit/component tests, 163 browser UI tests, 9 production-route tests, 3 style-studio tests and packaging. Final root integration verification passed all selected targets after isolating lifecycle publication in test fixtures. Child PR #59 merged as 7c1540377460bd80a8477c3c5607ce33020a23b3; this commit pins that merged revision. Final child/parent hooks validate branch ranges. No selected category was skipped; native installers, production deployment, live Stripe and real SMTP delivery are outside this task.

Request/service/model and background event loops are followed. Frontend API state, token recovery, desktop connectivity and composition remain in existing owners. A new SSE entitlement projection is intentionally not added: provider reads remain authoritative, and the existing subscription-change event refreshes mounted UI.

Auth follow-up: child refreshes rejected subscription tokens through the shared auth/config owners, bounds retries and stops repeated rejected-token focus requests. Dropdown direction/destructive tone, keyboard capture/toasts/menu ordering and profile role placement follow user review.
