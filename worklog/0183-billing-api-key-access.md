# Commit Title

feat(billing): allow application API keys on billing routes

# Changed File Scope

Billing router, authentication tests, provider/consumer OpenAPI contracts, bilingual billing and authentication guides, frontend submodule pin.

# Reason

Allow users to call all four billing operations with their existing application API key.

# Design

Reuse get_current_user and current_user_error_responses. Preserve owner binding, mixed credential validation and account deletion session requirements. Export the contract and coordinate a separate B4React contract PR before pinning it. Document request/response examples.

# Verification Plan

Run focused authentication and billing tests, root make verify-plan and make verify, child contract generation and required checks, staged and actual PR governance.

# Impact

Existing valid app keys gain billing access for their owner. No database, Stripe resource or response shape migration. Swagger advertises both schemes.

# Loop Alignment

Existing request/dependency/service/repository loop retained. No new domain event or background task: authentication-only change. No frontend runtime or UI change; only consumer contract/type synchronization.

# Verification

Focused billing/authentication suite: 29 passed. Root VERIFY_BASE=8d5e2f7 make verify-plan and make verify passed with full backend/frontend scope: 189 backend tests, architecture/env/contracts, 102 frontend tests, 71 UI tests, 6 production routes, 3 style studio tests, packaging and project build. Unchanged child results were reused by the verifier where eligible. Initial new test assertions were corrected to use the actual SDK positional customer argument and API-key list items envelope; final tests passed.

No checks omitted from the selected full plan. Real Stripe writes and live card registration were not run: the change is authentication-only and integration tests use isolated SQLite with a mocked provider. Frontend contract/types merged through B4React PR #35 (authored f10a8f0, merge 4166bcb); the parent pins that merge. No new background/event/UI loops are needed.
