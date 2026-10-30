# Commit Title

feat(auth): protect cookie refresh with session csrf tokens

# Changed File Scope

Backend auth service/token utilities, routes/contracts and security regressions; English/Korean security documentation. Frontend adoption is owned by child worklog 0109 and a subsequent parent integration commit.

# Reason

Cookie refresh currently accepts cross-site requests without a CSRF proof.

# Design

Synchronizer token stored in Redis per refresh session. A no-store bootstrap GET requires a custom header and valid refresh cookies; frontend retrieves the token before refreshing. Explicit body credentials remain supported without cookie fallback. No relational schema changes.

# Verification Plan

Focused security regressions, then VERIFY_BASE branch-wide make verify-plan and make verify; staged governance and actual PR metadata checks.

# Impact

Cookie clients must adopt the header; existing sessions bootstrap lazily. Redis expiry/logout removes CSRF state. Coordinate child-first frontend integration.

# Loop Alignment

Backend request/service/Redis/error and frontend API/recovery loops apply. No domain events/background jobs/UI composition changes; realtime and desktop reuse existing recovery.

# Verification

- Focused security/auth tests: 15 passed; frontend CSRF transport regressions: 2 passed.
- Branch-wide `REDIS_IN_MEMORY=true VERIFY_BASE=<merge-base> make verify-plan` and `make verify` passed: complete backend suite 507 passed, frontend 214 tests, 253 browser cases, 18 production-route cases, architecture/lint/contracts/tooling and packaging checks passed. Unchanged frontend receipts were reused on the second run.
- Initial run used the local external Redis setting and hit two unrelated account-deletion cooldown failures (429); rerun used isolated in-memory Redis without deleting external data. Existing deprecation warnings remain.
- Backend request/persistence/interface review: auth service orchestrates Redis utilities; no relational sessions, router business workflows or cross-service private access added. Events/background tasks and visual composition have no changes.
- No deployment or production-browser security test was run; API integration tests cover malicious simple requests and denied CORS preflight, and browser harness uses mocked API transport.
- Source commit precedes child contract provenance; child-first merge and final gitlink publication remain for the integration commit.
