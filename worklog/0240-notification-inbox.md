# Commit Title

feat(inbox): add persistent notification inbox

# Changed File Scope

Inbox data model/migration, authenticated API, SSE event, shared frontend inbox state/page and profile entry, localized docs and tests.

# Reason

Provide durable user-visible notifications independently of lifecycle email delivery, ready for the separate inquiry feature.

# Design

Scope update: center empty/loading states; add transactional welcome notifications for email/OAuth signup and deduplicated confirmed subscription-start/plan-change notifications independently of email delivery. Browser verification covers centered states and localized content.

User-owned inbox records persist in SQL. Reads and read-state writes always scope by current authenticated user, including admins. No public create endpoint. Internal producers can add notifications in their domain transaction. SSE carries invalidation only after commit; reconnect/focus reload authoritative DB state. Read-all uses a high-water ID so newly arriving notifications remain unread. No email or background job required.

# Verification Plan

Run root make verify-plan and make verify. Verify user isolation, read idempotency/high-water behavior, persistence and offline/reconnect UI recovery; browser checks reuse settings family.

# Impact

Additive migration and API. Public demo has no access to inbox data. No container image build/publication.

# Loop Alignment

Router/service/repository with auth guards and central typed errors. Post-commit domain event refreshes page/header state. Background tasks are not applicable to immediate durable inbox writes. Existing desktop recovery and UI composition are retained.

# Verification

Backend architecture/env/lint/contracts and 468 tests passed, including ownership, welcome creation, duplicate confirmed billing notification delivery with EMAIL_ENABLED=false and pending-change suppression. Applied additive migration 0018 to the local DB after detecting an already applied 0017; records were preserved. Root classifier selects backend plus full frontend checks. Frontend completion and merged child pin recorded below. No container image build/publication.

Final root make verify-plan/verify passed: backend 468, frontend 165 unit/component and 201 UI browser cases, production route/style-studio checks, contract/package checks and project-build test. Full scope was selected; container image and desktop publication omitted as not requested.

Integrated B4React PR #76 via merge commit 214ae25d1fdbc0d0a72632bbb1f4c21a66fe9a71; local hooks and actual PR governance passed.
