# Commit Title

feat(admin): add opt-in public administrator demo

# Changed File Scope

Admin demo API, runtime configuration, contracts, frontend integration and localized documentation.

# Reason

Let visitors explore administrator screens using real server health and anonymized user records.

# Design

DEMO_ENABLED defaults false. Dedicated read-only public endpoints reuse administrator contracts, project non-identifying user fields, pseudonymize identifiers with domain-separated HMAC, round dates to UTC days, and search only aliases. Host addresses are removed. Thirty-second process-local snapshots limit public probes. Existing administrator authorization remains unchanged; no migration.

# Verification Plan

Root make verify-plan and make verify against branch base; privacy, access control, config and browser navigation checks. Child PR merges before parent gitlink update.

# Impact

Explicit opt-in publishes counts, roles, activity flags, day-level dates and server health. Disabled mode returns 404. Snapshots may lag thirty seconds.

# Loop Alignment

Request/service/repository and central errors are retained. Read-only queries need no domain event or background task. Frontend retains API state, cancellation and connectivity recovery; no mutation realtime event.

# Verification

Root make verify-plan selected backend plus full frontend scope. make verify passed architecture/env/lint/format checks, 466 backend tests, OpenAPI export/child contract checks, 165 frontend unit/component/integration tests, 196 browser tests, 10 production route tests, 3 style-studio browser tests and project initialization/build checks. Backend privacy/access tests cover aliases-only search, filters/pagination, guest status access, disabled warm caches, safe errors and coalescing. Existing administrator roles remain protected. No selected checks omitted; unchanged child checks were reused through content-bound receipts. No new event/task loop is needed because the feature is read-only.

B4React PR #74 merged with merge commit 8f11702dbc9186b4725857a895b4848b9927f99e; parent pins that merged commit. Demo remains off by default; deployment requires DEMO_ENABLED=true.
