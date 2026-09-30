# Commit Title

ci: move automated verification to local Git hooks

# Changed File Scope

Versioned Git hooks, installer and hook tests; verification receipts; manual workflows, ruleset, Make hooks and English/Korean guidance. Parent also integrates the merged B4React pin.

# Reason

Avoid repeated local, child CI and parent CI verification waits while preserving local checks and PR-based integration, as explicitly requested by the user.

# Design

commit-msg validates the staged worklog and actual message. pre-push validates all authored branch commits and the exact clean pushed HEAD against remote main, then runs change-scoped Make verification. Successful local command receipts may be reused only for identical source/config/tool context; text and governance always rerun. GitHub workflows become manual-only. Remove only required status checks from live rulesets; retain PR, conversations, deletion and non-fast-forward protection.

# Verification Plan

Run isolated real-Git hook acceptance/rejection fixtures, cache invalidation tests, workflow checks, make verify-plan and make verify. Exercise installed hooks during this task commit/push, validate actual PR metadata locally, and read back live GitHub rules. Merge the child first, then parent.

# Impact

No app/API behavior changes. Automatic PR/push/schedule/tag/release jobs stop; manual workflows remain. Hooks must be installed per clone and remain bypassable locally. No remote CI attestation is claimed.

# Loop Alignment

Infrastructure-only: backend request/event/background and frontend API/realtime/connectivity/UI loops are not applicable; their existing test targets are retained in local verification.

# Verification

Root make verify-plan selected full backend/frontend scope for protected tooling and policy edits. make verify passed all selected targets: hook/receipt fixtures (8+6), project initialization checks/tests, backend architecture/env/lint and 119 backend tests, contract check, 98 frontend tests, 71 UI cases, six production route/build cases, three style-studio cases, packaging and six isolated branding cases. Existing scope-classifier fixtures (13) passed; no scope was downgraded. actionlint 1.7.12 validated all manual workflows. make hooks-install activated hooks in both clones. Live rulesets 16499496 and 24035784 were updated/read back: only required status checks were removed, all other fields preserved exactly. API/UI runtime loops not applicable because this is infrastructure. Manual remote workflows were not dispatched to avoid duplicate execution; equivalent local checks passed. Child commit c5e7e08 passed the installed commit-msg/pre-push hooks; actual PR #33 metadata passed locally, with zero automatic status checks. Child PR #33 merged by merge commit; its tree matches the tested authored commit. Parent push runs installed hooks before publication.
