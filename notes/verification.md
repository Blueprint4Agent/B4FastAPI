# Change-scoped verification

`make verify-plan` shows affected **areas**, application regression depth, and selected
commands. `python3 scripts/verification.py plan --json` also exposes each changed
file's ownership. `make verify` runs that plan. Git governance remains mandatory.

## Ownership and regression depth

Area and depth are independent: an authentication change keeps broad application
regressions without automatically running unrelated editor or discovery tooling.
Plans compose the union of all changed areas, including pinned and dirty child changes.

| Changed area                                                             | Selected checks                                                                                                     |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| Markdown documentation anywhere                                          | UTF-8, whitespace and JSON checks; no runtime dependencies                                                          |
| AGENTS/domain/test guides, worklog template, Git hooks                   | Governance/harness fixtures plus text validation                                                                    |
| Existing locale string values with identical shape/placeholders/markup   | Text/JSON only                                                                                                      |
| Locale key/shape changes                                                 | Broad frontend application checks, unit/UI and production-route tests                                               |
| Backend application/tests/migrations/dependencies                        | Backend lint, architecture, complete security/data suite and contract checks                                        |
| Frontend application/auth/API/shared state                               | Application static/type/API/format checks, unit tests; UI/browser and production routes according to depth          |
| Contracts                                                                | Provider/consumer baseline checks, frontend types/application/unit/production routes                                |
| Docker/deployment                                                        | Env/initializer checks and fake-Docker orchestration tests; no live deployment                                      |
| Public discovery tooling                                                 | Discovery fixtures and isolated static build/browser checks; parent IndexNow tools have separate publication checks |
| Style studio                                                             | Application regression checks, editor file-access fixtures and editor browser suite                                 |
| Branding                                                                 | Public identity fixtures, production build/routes; parent adds isolated customized build                            |
| Verification harness                                                     | Classifier, scheduler, receipts and governance fixtures                                                             |
| Shared build inputs (Makefile/Vite/dependencies/CI) or unknown ownership | All repository areas                                                                                                |

The application risk levels remain `none/docs/copy/behavior/ui/full` for existing
consumers. `full` depth means broad application coverage; `VERIFY_FULL=1` means
**all areas**. Root and nested AGENTS guides are governance, other Markdown is
text only. A missing comparison revision expands to all areas. Invalid/deleted
locale data expands application checks; malformed JSON also fails lightweight validation.
Shared CSS retains broad app checks; shared app.css changes additionally select style studio and discovery because both
consume its tokens/styles. Reviewed billing/admin-only CSS keeps its scoped selection.
Structural changes to discovery/home.project locale data and editor API/locales select
their actual tool consumers too. Unknown impact within the app retains
broad app suites. No manual skip/downgrade flag is provided.

Existing reviewed billing/admin selections remain supported. Backend domain selection remains a follow-up (#152); this change does
not infer safe backend subsets from filenames. Backend auth/security/data tests
remain complete. A new locale key does not imply that browser tests can be skipped.

## Commands and compatibility

```sh
make verify-plan
make verify
VERIFY_BASE=$(git merge-base origin/main HEAD) make verify
VERIFY_FULL=1 make verify
VERIFY_FULL=1 VERIFY_JOBS=1 make verify # identical checks, sequential command lanes
python3 scripts/verification.py plan --json
```

The default comparison includes staged, unstaged and untracked changes against HEAD.
Use VERIFY_HEAD for an immutable endpoint. Manual Actions/CI keep all areas and
ignore receipts. `--domain backend|frontend` retains separate manual CI jobs;
root governance is validated independently of application-domain filtering.

`check-app` runs static application policy, types, formatting and generated API drift
without unrelated harness fixtures. `verification-harness-test` runs isolated Python
fixtures; `app-tooling-test` runs static-checker fixtures. `test-production` builds and
checks production routes. Existing `check`, `hooks-test`, `test-routes` and other
standalone Make commands remain available; `test-routes` still includes discovery.

## Bounded parallel execution

The runner defaults to `VERIFY_JOBS=2`. Independent backend checks can overlap the
ordered frontend pipeline. `VERIFY_JOBS=1` / `--jobs 1` keeps sequential scheduling
for comparison or constrained machines. This controls command lanes, not individual
test worker counts. Backend pytest remains sequential: no xdist dependency or
unverified DB/process isolation change is introduced.

Frontend generators, checks, builds, browser suites and isolated custom-brand builds
retain order. Browser suites share report output/fixed ports; they must not run as
separate concurrent commands. Packaging waits for all preceding checks, including
backend static-serving tests, before replacing backend dist. The app Playwright
config enables `fullyParallel` for independent browser contexts while retaining the
existing worker budget (CLI `--workers` remains supported). Production/editor/
discovery suites retain their existing scheduling.

On failure, no new commands start; already-running commands finish before the runner
returns nonzero. Downstream packaging cannot run after failure. Each invocation has
its own log directory in `.git/verification-logs/run-*`; concise progress prints
command durations and the final wall time, with failure excerpts and complete logs.
Do not start two verification runners concurrently against the same checkout.

Playwright's independent-case scheduling follows its [parallelism documentation](https://playwright.dev/docs/test-parallel).
Browser fixtures use per-test contexts and request mocks; no suite-level shared
page, ordered workflow across tests or developer backend is used by app E2E tests.

## Receipts and integration

Successful unchanged local commands may reuse content-bound receipts for up to 24h.
Source/configuration/tool/environment/output changes invalidate them; command scope
is part of the key. Text/Git governance always run. Worklog-only result edits still
receive text and governance validation. Forced full and CI neither reuse nor save
receipts. Failed commands invalidate their prior receipt.

Follow child-first integration: merge the B4React task PR, then update the parent
pin. Parent contracts and packaging still run. Keep related edits in one task PR,
record selected/omitted checks and reasons, and do not repeat successful unchanged
checks as separate check/test/ci rituals. See [local hooks](local-hooks.md).

## Historical measurements

The measurements below describe the 2026-10-07 implementation and revision range,
not current universal timing guarantees. For this ownership/parallel change, use
the observed results and scope recorded in the matching worklog.

## Measured results — 2026-10-07

The existing billing/admin UI change was used as the benchmark: B4React
`ca3f83f..57a67d5`, B4FastAPI `06e55ba..7c4922e`. Timings are single local
wall-clock samples from `/usr/bin/time -p`, not a guarantee for every change.

| Scenario                                  |                                              Before |       After |
| ----------------------------------------- | --------------------------------------------------: | ----------: |
| First UI verification                     |                                            121.01 s | **30.72 s** |
| Identical UI verification repeated        | Expensive checks were repeated in hooks/integration |  **1.08 s** |
| Parent integration of the same UI change  |                                            122.36 s |  **1.65 s** |
| Unit/component/integration cases selected |                                                 140 |      **39** |
| Browser cases selected                    |                                                 164 |      **32** |

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

| Scenario                                    | Before                                          | After                                                  |                          Previous time |      New time | Evidence                                                     |
| ------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------ | -------------------------------------: | ------------: | ------------------------------------------------------------ |
| Registered billing/admin rendering edit     | All unit/browser cases                          | Affected components/render scenarios and related tests |                               121.01 s |       30.72 s | Measured UI revision range                                   |
| Unchanged repeated verification             | Hooks/integration could repeat expensive checks | Reuse matching successful receipts                     | No separate identical-command baseline |        1.08 s | New behavior measured                                        |
| Parent integration of that UI edit          | Repeat child checks/build                       | Reuse child proof; retain contracts/packaging          |                               122.36 s |        1.65 s | Measured                                                     |
| Backend only                                | Backend suite                                   | Backend suite retained                                 |                             About 45 s |    About 45 s | Estimate from roughly 44 s backend stage                     |
| That UI edit plus backend changes           | Broad UI plus backend                           | Affected UI plus backend                               |                            About 165 s |    About 75 s | Sum-of-stages estimate                                       |
| Verification scripts, auth or shared config | Broad/full checks                               | Broad/full checks retained                             |                          Roughly 200 s | Roughly 200 s | Full-run reference, not a controlled before/after comparison |

The 30 s UI figure applies to this registered render-only case, not arbitrary shared CSS,
global state or dependency changes. Backend tests are not blindly selected by changed filenames.
The 45 s/75 s values are estimates rather than separately measured end-to-end totals. Reuse
requires matching source/configuration/toolchain/selected suites, valid age and build outputs;
it never carries old successful proof across a changed implementation.

## Backend test environment

Root `backend-test` and `deployment-check` set `TRACING_ENABLED=false` for pytest.
This isolates tests from developer OTLP exporters and avoids native gRPC fork crashes
in macOS subprocess fixtures. Runtime `.env` is unchanged; tracing-specific tests may
explicitly opt in with a mocked exporter. See the backend test guide.

## Reviewed page ownership (#94)

The file-level registry now covers home (HomePage/ProjectOverview/legacy LandingPage),
profile, support, inbox and prompt-builder as well as billing/admin. Home owns
`home.spec.ts`; runtime/auth/shared-shell checks stay in `runtime-modes.spec.ts`.
Profile retains account/profile-photo browser cases and related component/hook tests;
prompt-builder retains its component and pure-logic tests. Support/inbox currently
have browser coverage rather than dedicated Vitest files: selecting their complete
browser files does not invent unrelated unit work. Multiple owners form a deduplicated
union. Unknown/shared components, auth/recovery/API transport, shared CSS and the
app-wide InboxProvider still broaden. Missing mapped coverage also broadens.
The new pages use test-file ownership, not per-JSX title registration. Selected paths
appear in the plan and command-bound receipt keys. Production-route receipts bind dist
contents too; missing/changed builds cannot authorize packaging.

Support mutations run once per role, inbox mutation/retry/reload once, and viewport/theme
cases start with prepared populated/closed/empty state. Billing paid/manual mutations
and error recovery have representative business owners; their geometry matrices retain
responsive/theme checks. Home repeats business navigation once and keeps the shell/footer
matrix. Provider/security cases and actual geometry/color assertions remain. The old
fixed marketing-card count and private danger/text CSS class spellings are not product
contracts. Legacy loginEnabled variants share one parameterized assertion body, and retry
still asserts no window drag both before and after clicking.

Successful screenshots are review artifacts, not pixel assertions. Playwright automatically
captures failures; use `B4F_CAPTURE_VISUALS=1 make test-ui` for optional successful review
images (also supported by discovery/editor suites). Direct screenshot assertions added in
future remain independent of this artifact helper. No tests are skipped by this flag.
Small-page first/repeat/parent timings are recorded in the matching worklog, not enforced
as a wall-time gate. Backend domain selection remains a separate #152 task.
