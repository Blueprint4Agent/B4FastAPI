# Commit Title

feat(frontend): integrate verified account experience

# Changed File Scope

Pinned src/frontend gitlink and this integration worklog.

# Reason

Ship the B4React account/settings/feedback changes alongside the matching backend
proof and mail contract in the same parent task PR.

# Design

Consume merged B4React PR #29, including its local provider snapshot/types, existing
shared controls, isolated code-entry showcase, inset modal scroll/focus rules and
EN/KO documentation. No parent-owned frontend source or generated contract writes.

# Verification Plan

Use root full-scope plan against the original main baseline. Reuse completed delegated
child check/test/UI/routes/studio evidence for unchanged content, verify contract and
packaging integration and the custom-brand project-build harness. Require governance
and code CI for both child and parent; merge commits only.

# Impact

Settings displays Account with mailbox-verified deletion at the bottom. Legacy Profile
URLs still resolve. Toasts carry transient send/cooldown feedback; proof errors stay
inline. Child modal fixes preserve existing themes and shared controls.

# Loop Alignment

Frontend API/session ownership stays in existing hooks/AuthProvider; proof request
state is scoped to the current owner. UI composition is shared with showcase. No new
realtime/polling loop is needed for explicit deletion; other sessions are rejected on
subsequent authenticated requests. Desktop recovery remains in the existing coordinator.
Backend request/background loops are documented in worklog 0175.

# Verification

Root make verify-plan/make verify selected backend plus full frontend scope. After
fixing initial test assertions, delegated final make check test passed 95 tests;
make test-ui passed 69 cases; frontend-test-routes passed six production cases;
make test-style-studio passed three cases. Contract semantic agreement, verified-dist
packaging and project-build-test with custom-brand production routes passed.
Root project init, environment, backend architecture/Ruff/test checks passed as recorded
in 0175. No selected checks omitted or downgraded; passing unchanged child/runtime
checks are reused after the merge gitlink update. Required CI is checked separately.

B4React #29 passed required Frontend checks and Git governance and merged via merge
commit 2d4f1edd028c914a9ab546adef14d5e182749824. Its tree equals the tested feature
head, including the contrast-test timing correction (69 browser cases rerun locally).
The parent's first CI run passed 118 backend tests but correctly rejected the old
child contract pin; updating this gitlink resolves that integration mismatch. Root
frontend-contract-check passes for the merged child. Parent CI reruns on this commit.
