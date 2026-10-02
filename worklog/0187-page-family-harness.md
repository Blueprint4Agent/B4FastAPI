# Commit Title

chore(frontend): integrate page family consistency harness

# Changed File Scope

Root agent guide, frontend gitlink and integration worklog.

# Reason

Future sessions need page-family rules and enforced review, beyond shared-control and stylesheet ownership checks.

# Design

Point root guidance to the child canonical page-family policy. Integrate UI review governance, settings-header structural guard and acceptance/rejection fixtures. Preserve snapshot-scoped historical commit policy.

# Verification Plan

Child full scoped Make verification and fixture tests; parent full branch verification after child merge, including package/contracts and Git governance.

# Impact

UI edits require documented peer comparisons, shared rules and scoped exceptions; known header nesting regression fails static checks. Static checks do not prove universal visual equality.

# Loop Alignment

Strengthens the UI composition review loop. API, realtime, desktop connectivity and backend event/task behavior remain unchanged.

# Verification

B4React PR #39 merged at 4a4b822. Child full verification and composition/governance rejection fixtures passed. VERIFY_BASE=8d5e2f7 make verify-plan selected backend + full frontend; make verify passed hooks, backend/contract checks (189 tests), frontend check/test (110), browser UI (79), production routes (7), style studio (3), package/contracts and project build tests. No selected checks omitted. Real Stripe/native execution is not applicable to guidance and local harness changes.
