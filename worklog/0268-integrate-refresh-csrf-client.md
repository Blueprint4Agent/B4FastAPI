# Commit Title

feat(auth): integrate csrf-aware refresh client

# Changed File Scope

src/frontend gitlink and this integration worklog.

# Reason

Publish the backend CSRF enforcement with its matching browser refresh handshake.

# Design

Merge the B4React CSRF task PR first, then pin its reviewed merge commit. Provider contract is owned by commit 60808d78bcdc8f6b799b89814af59cf66a4e9fa0 and worklog 0267. No additional runtime implementation.

# Verification Plan

Run branch-wide REDIS_IN_MEMORY=true VERIFY_BASE=<merge-base> make verify-plan and make verify, staged governance and actual ready PR metadata checks. Reuse valid unchanged child receipts.

# Impact

Deploy parent and pinned frontend together. Existing sessions lazily bootstrap proof; older clients fail refresh without a proof. No migration.

# Loop Alignment

Backend auth request and frontend API/session recovery loops reviewed in provider worklog 0267 and child worklog 0109. No events/tasks, new rendering or desktop orchestration.

# Verification

- B4React PR #101 merged with merge commit addd14ac4d739e511ae043aa3ac865b3ca82c4df; actual title/body/label/base/head/draft metadata and PR governance checked before merge.
- Full branch `REDIS_IN_MEMORY=true VERIFY_BASE=<origin/main merge-base> make verify-plan` and `make verify` passed after pinning the merge: 507 backend tests, 214 frontend tests, 253 browser cases and 18 production-route cases; harness, architecture, formatting, contract freshness/compatibility and frontend packaging passed.
- Child standalone verification and push hook also passed. Initial external-Redis cooldown failures and isolated rerun are recorded in worklog 0267.
- No production deployment or real production-browser attack test; browser suites use mocks, and backend integration tests exercise actual request/service/session validation. No checks selected by the planner were omitted.
- Parent publication is a ready PR, without a main merge or deployment.
