# Commit Title

fix(verification): integrate scoped CSS ownership

# Changed File Scope

Mirrored CSS resolver/classifier fixtures, verification notes and merged frontend pin.

# Reason

Home-only footer CSS incorrectly selected all application browser cases plus editor/discovery. Roll back the abandoned footer UI and resolve CSS ownership from actual runtime consumers rather than billing/admin names alone.

# Design

Require a bounded class-anchored selector, known domain consumers and existing coverage. Compose domains; shared/global/sibling escape/unsupported syntax/unknown consumers widen. Mirror parent and child policies; retain independent child execution. No UI/runtime API change.

# Verification Plan

Test scoped Home/profile/inbox CSS, multi-domain unions, missing/shared consumers, global selectors/tokens/keyframes and unsafe selector escapes. Reproduce the original footer diff as a plan-only fixture, then run Make verify-plan/verify, branch governance and child-first PR integration. Finish docs before verification to avoid needless receipt invalidation.

# Impact

Existing UI restored. Future page-owned CSS chooses related tests; shared and unknown styles keep broad checks. No manual skip flag or receipt-policy change.

# Loop Alignment

Verification tooling only: request, domain event, background task, API state, realtime, desktop recovery and UI composition runtime loops are not changed.

# Verification

Root make verify-plan / make verify passed in 9.7 s (run-b7tcbmgt): root harness command and reused matching child harness proof. Child has 65 passing fixtures (9.9 s first run). All three scope/planner and fixture mirrors agree. Actual footer padding replay selects Home unit/browser/static/build and excludes whole UI/editor/discovery; source was restored. Explicit-full and global/shared/unsafe/missing-coverage fixtures preserve broad fallback. App UI/CSS is unchanged, so backend, application UI/browser/build/contracts/packaging checks were omitted by the classifier. Child B4React PR #98 merged first at 1f56a3ab755593e5a1b447678c046bc2a6271a33. No deployment or receipt-policy change.
