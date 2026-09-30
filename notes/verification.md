# Change-scoped verification

Use `make verify-plan` to inspect the plan and `make verify` to execute it. Local hooks and manual Actions use `scripts/verification.py`; Git governance remains independent and mandatory. This policy supersedes unconditional pre-commit check/test/build lists for low-risk edits.

| Scope | Classification | Verification |
| --- | --- | --- |
| Docs | Known Markdown documentation/worklog paths, excluding AGENTS.md | Changed text, whitespace and UTF-8 validation |
| Copy | Existing locale JSON string values only; identical keys, placeholders, nesting references and markup | Text/JSON validation including duplicate-key rejection |
| Behavior | Non-protected runtime utilities/hooks/tests; backend application/tests | Affected domain checks and tests; frontend build |
| UI | Components/pages/styles/assets/browser tests | Frontend checks/tests/build and browser UI suite |
| Full | Auth/session/API/connectivity, contracts, dependencies, configuration, CI/tooling, unknown paths or unavailable history | Full affected checks, production routes and style editor; parent integration/packaging checks |

Mixed changes take the strongest scope. Backend application changes retain the entire backend suite, including security/data paths; there is no unsafe per-file test guessing. Frontend Vitest is also retained for runtime changes because it is fast and protects shared dependencies. No downgrade flag or PR label bypass exists. Locale additions/deletions, renamed keys, altered interpolation/markup, arrays and non-string values require full verification. The classifier is conservative; agent judgment can escalate validation and add a focused visual check when copy affects wrapping.

Default comparison is HEAD to the current working tree (including staged and untracked files). For a whole branch use `VERIFY_BASE=$(git merge-base origin/main HEAD) make verify`. The push hook compares remote main merge-base to the exact clean pushed HEAD, so follow-up commits cannot conceal earlier runtime changes. Manual Actions use full verification. `VERIFY_FULL=1 make verify` forces full checks; `make verification-test` exercises actual Git fixtures.

The parent inspects both frontend gitlink endpoints and local dirty child changes. A copy-only child pin update can avoid runtime checks; missing child history selects full frontend verification. The repositories carry the same classifier/test source intentionally to keep the child independent; keep these copies synchronized when changing policy. Parent runtime pins still receive contract/package checks. Lightweight validation does not require npm/uv or read local environment secrets.

GitHub workflows are manual-only; required status checks are removed. PRs, resolved conversations, deletion/force-push protection and zero required approvals remain. See [local hooks](local-hooks.md).

Do not rerun a successful delegated check for the same relevant content. Record the command, compared revision/scope and skipped checks in the worklog. New runtime edits invalidate prior runtime evidence; copy-only follow-ups need only their selected checks locally. The push hook validates the complete branch. Keep related edits in one task PR, merge the child once, then update the parent pin. Read local log summaries and failure excerpts. Content-bound command receipts can reuse unchanged successful local checks for up to 24 hours; source/config/tool/output changes or failures invalidate them. Text and governance checks always run. Worklog-only result updates do not invalidate expensive checks. VERIFY_FULL=1 and manual Actions disable reuse.

The runner prints a concise scope/command summary and timing. Full command output is stored in the repository Git directory under `verification-logs/`; on failure it prints the last 80 lines and exits nonzero. `python3 scripts/verification.py plan --json` exposes the complete machine-readable plan. Full parent verification packages the production-route-tested dist without rebuilding it; custom-branding isolation remains a separate check.
