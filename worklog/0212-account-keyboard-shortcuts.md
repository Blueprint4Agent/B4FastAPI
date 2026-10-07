# Commit Title

feat(auth): persist account keyboard shortcuts

# Changed File Scope

User schema/repository, profile service, migration 0014, OpenAPI, backend tests/docs. Frontend source is committed separately in B4React; the parent gitlink adopts B4React PR #63 merge commit 93591c1b5fee7db9f0f55bfd0347645935bdc5e1.

# Reason

Replace browser-owned shortcut settings with durable account-owned database settings.

# Design

Extend existing authenticated GET/PATCH /auth/me with validated keyboard_shortcuts JSON. Null resets defaults; omitted fields preserve existing values. Frontend adopts explicit contract and uses AuthProvider profile updates.

# Verification Plan

Initial plan: root make verify-plan and make verify plus persistence/account/browser checks. User later explicitly stopped full verification; retain focused test and browser evidence, and run staged Git governance before the requested commits.

# Impact

Existing accounts default to standard bindings. Legacy browser data is ignored to avoid importing shared-browser preferences into an arbitrary account. Apply migration before serving.

# Loop Alignment

Request/router/service/repository loops retained. Existing auth bootstrap and desktop recovery refresh server state. No realtime event or worker: small synchronous profile preference updates become visible on reload/login/recovery, not pushed to other active tabs.

# Verification

User explicitly stopped full verification for this task. Root make verify-plan selected backend + full frontend (auth/contract changes); make verify was interrupted during backend checks, so no full-pass claim is made. The user subsequently requested commits, pushes, ready PRs and automatic merge commits. Required local pre-push checks run without bypass; no separate manual full rerun is requested. Hooks, backend architecture, Ruff lint/format passed before interruption. Focused backend shortcut/runtime-mode tests: 16 passed. B4React typecheck passed; focused shortcut integration/unit tests: 6 passed. Live localhost:5173 B4React authenticated screen saved Command+Shift+B through the profile API, retained it after reload, reset to Command+B and retained reset after another reload. Guest screen showed disabled edit/reset controls. Screenshot: /tmp/b4react-keyboard-db.png. Local database reports 0014_keyboard_shortcuts at head. The first manual run omitted UI/routes/style-studio/packaging after user interruption. The later authorized push workflow requires the repository pre-push harness; its outcomes are recorded below.


B4React PR #63 passed actual PR governance and merged with two-parent merge commit 93591c1. Its full pre-push harness passed 143 tests, 164 browser scenarios, static checks, production routes and style-studio; the worklog-only follow-up reused these receipts. Parent integration keeps contract/packaging checks.

Parent pre-push passed hooks-test, project initialization/architecture/environment/Ruff checks, all 291 backend tests, contract freshness and provider/consumer parity, branding, frontend packaging and isolated project build tests. Unchanged child check/test/UI/routes/style-studio receipts were reused, not rerun. Full selected verification passed on 9eb00a6; logs: /tmp/keyboard-parent-push.log and .git/verification-logs/.
