# Change-scoped verification

Use `make verify-plan` to inspect the plan and `make verify` to execute it. Local hooks and manual Actions use `scripts/verification.py`; Git governance remains independent and mandatory. This policy supersedes unconditional pre-commit check/test/build lists for low-risk edits.

| Scope | Classification | Verification |
| --- | --- | --- |
| Docs | Known Markdown documentation/worklog paths, excluding AGENTS.md | Changed text, whitespace and UTF-8 validation |
| Copy | Existing locale JSON string values only; identical keys, placeholders, nesting references and markup | Text/JSON validation including duplicate-key rejection |
| Behavior | Non-protected runtime utilities/hooks/tests; backend application/tests | Affected domain checks and tests; frontend build |
| UI | Components/pages/styles/assets/browser tests | Frontend checks/tests/build and browser UI suite |
| Full | Auth/session/API/connectivity, contracts, dependencies, configuration, CI/tooling, unknown paths or unavailable history | Full affected checks, production routes and style editor; parent integration/packaging checks |

Mixed changes take the strongest scope. Backend application changes retain the entire backend suite, including security/data paths; security/data paths are not narrowed by filename guessing. Frontend checks/types remain global; mapped billing/admin changes select their registered unit/integration and browser suites. Shared or unmapped changes retain broad suites. No downgrade flag or PR label bypass exists. Locale additions/deletions, renamed keys, altered interpolation/markup, arrays and non-string values require full verification. The classifier is conservative; agent judgment can escalate validation and add a focused visual check when copy affects wrapping.

Default comparison is HEAD to the current working tree (including staged and untracked files). For a whole branch use `VERIFY_BASE=$(git merge-base origin/main HEAD) make verify`. The push hook compares remote main merge-base to the exact clean pushed HEAD, so follow-up commits cannot conceal earlier runtime changes. Manual Actions use full verification. `VERIFY_FULL=1 make verify` forces full checks; `make verification-test` exercises actual Git fixtures.

The parent inspects both frontend gitlink endpoints and local dirty child changes. A copy-only child pin update can avoid runtime checks; missing child history selects full frontend verification. The repositories carry the same classifier/test source intentionally to keep the child independent; keep these copies synchronized when changing policy. Parent runtime pins still receive contract/package checks. Lightweight validation does not require npm/uv or read local environment secrets.

GitHub workflows are manual-only; required status checks are removed. PRs, resolved conversations, deletion/force-push protection and zero required approvals remain. See [local hooks](local-hooks.md).

Do not rerun a successful delegated check for the same relevant content. Record the command, compared revision/scope and skipped checks in the worklog. New runtime edits invalidate prior runtime evidence; copy-only follow-ups need only their selected checks locally. The push hook validates the complete branch. Keep related edits in one task PR, merge the child once, then update the parent pin. Read local log summaries and failure excerpts. Content-bound command receipts can reuse unchanged successful local checks for up to 24 hours; source/config/tool/output changes or failures invalidate them. Text and governance checks always run. Worklog-only result updates do not invalidate expensive checks. VERIFY_FULL=1 and manual Actions disable reuse.

The runner prints a concise scope/command summary and timing. Full command output is stored in the repository Git directory under `verification-logs/`; on failure it prints the last 80 lines and exits nonzero. `python3 scripts/verification.py plan --json` exposes the complete machine-readable plan. Full parent verification packages the production-route-tested dist without rebuilding it; custom-branding isolation remains a separate check.

## Affected suites and local reuse

`make verify-plan` (or `python3 scripts/verification.py plan --json`) reports affected suites.
Billing/admin page, feature and domain-hook edits select registered domain coverage. CSS is
narrowed only when every changed rule is scoped to those domains; shared selectors, variables,
keyframes or unsupported syntax retain all UI tests. Test-body-only browser edits select the
whole generated test group by source line; setup changes/deletions select the full spec.
Missing coverage, protected auth/API/config changes and unknown impact fail broad. Backend
application changes still run the backend suite because authorization/data coupling is shared.

Static checks/types, contracts, builds and Git governance are retained. Unit/browser selection
is visible in the plan and encoded in each receipt command, so one subset cannot authorize another.
Full/CI verification ignores scoped selection and receipts. Use `VERIFY_FULL=1 make verify`.

Use one shell/toolchain throughout a task: from the parent run `make -C src/frontend verify`
and `git -C src/frontend push`, then root integration. Equivalent PATH duplicate entries and
Git's injected helper path no longer invalidate receipts. Real PATH precedence/tool versions,
resolved executables, config, source, expired receipts and changed build outputs still invalidate.
Different Python installations between shells correctly require new checks. Cache misses print
which key changed without exposing configuration values. Branding is generated before child
checks; parent integration reuses child build/routes receipts and always validates contracts/packages.

For registered components, edits confined to the JSX return region (unchanged setup/helpers
and trailing code) select reviewed render scenarios by stable title markers. CSS owner lookup
must resolve every changed selector to registered components; otherwise the domain suite remains.
Missing/renamed markers fail back to the complete domain suite. Hook logic edits keep domain-wide
coverage. Scoped browser cases run in isolated contexts with the configured worker limit and
fully-parallel scheduling. Mapped changes use `check-affected`: global type/architecture/UI/state
policy checks plus changed-file formatting, without rerunning unchanged tooling self-tests or
regenerating an unchanged API contract. Tooling/config changes still select full `check`.

## Measured results — 2026-10-07

The existing billing/admin UI change was used as the benchmark: B4React
`ca3f83f..57a67d5`, B4FastAPI `06e55ba..7c4922e`. Timings are single local
wall-clock samples from `/usr/bin/time -p`, not a guarantee for every change.

| Scenario | Before | After |
| --- | ---: | ---: |
| First UI verification | 121.01 s | **30.72 s** |
| Identical UI verification repeated | Expensive checks were repeated in hooks/integration | **1.08 s** |
| Parent integration of the same UI change | 122.36 s | **1.65 s** |
| Unit/component/integration cases selected | 140 | **39** |
| Browser cases selected | 164 | **32** |

The final first run spent 9.3 s on static policy/types/changed-file formatting,
2.2 s on related unit/integration tests, 13.2 s on browser scenarios and 4.9 s
on the build, plus runner overhead: approximately **75% less wall time**.
Parent integration still checked contracts and packaged the verified build.
The earlier domain-only iteration took 101.16 s; the final 30.72 s additionally
uses render ownership, affected checks and isolated parallel browser scheduling.

The original child login shell used Python 3.9 while the parent used Python 3.14.
Follow-up commands use one root shell via `make -C` / `git -C`; this environment
standardization is part of the workflow improvement, so these are workflow
measurements rather than an isolated microbenchmark of the selector alone.
Real toolchain changes still invalidate receipts. No live payment or email was sent.

Backend-only verification has not been separately benchmarked here: the backend
stage measured approximately 44 s, so roughly 45 s for backend-only and roughly
75 s for this UI change plus backend work are **estimates**, not measured totals.
Protected/shared/unknown changes keep broader verification (about 200 s in the
full harness run). Cache reuse is conditional on unchanged inputs and outputs.

Commands used for the final UI measurements:

```sh
VERIFY_BASE=ca3f83f VERIFY_HEAD=57a67d5 make -C src/frontend verify
# Repeat the same command to measure receipt reuse.
VERIFY_BASE=06e55ba VERIFY_HEAD=7c4922e make verify
```

Raw local logs: `/tmp/b4-verify-baseline-first.log`,
`/tmp/b4-verify-baseline-integration.log`, `/tmp/b4-verify-refined-first.log`,
`/tmp/b4-verify-refined-repeat.log`, `/tmp/b4-verify-refined-integration.log`.
The benchmark intentionally evaluates the already-merged UI revision range.
The verification-tool changes themselves are separately checked at full branch scope.

### Before/after by change scenario

| Scenario | Before | After | Previous time | New time | Evidence |
| --- | --- | --- | ---: | ---: | --- |
| Registered billing/admin rendering edit | All unit/browser cases | Affected components/render scenarios and related tests | 121.01 s | 30.72 s | Measured UI revision range |
| Unchanged repeated verification | Hooks/integration could repeat expensive checks | Reuse matching successful receipts | No separate identical-command baseline | 1.08 s | New behavior measured |
| Parent integration of that UI edit | Repeat child checks/build | Reuse child proof; retain contracts/packaging | 122.36 s | 1.65 s | Measured |
| Backend only | Backend suite | Backend suite retained | About 45 s | About 45 s | Estimate from roughly 44 s backend stage |
| That UI edit plus backend changes | Broad UI plus backend | Affected UI plus backend | About 165 s | About 75 s | Sum-of-stages estimate |
| Verification scripts, auth or shared config | Broad/full checks | Broad/full checks retained | Roughly 200 s | Roughly 200 s | Full-run reference, not a controlled before/after comparison |

The 30 s UI figure applies to this registered render-only case, not arbitrary shared CSS,
global state or dependency changes. Backend tests are not blindly selected by changed filenames.
The 45 s/75 s values are estimates rather than separately measured end-to-end totals. Reuse
requires matching source/configuration/toolchain/selected suites, valid age and build outputs;
it never carries old successful proof across a changed implementation.
