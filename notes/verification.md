# Change-scoped verification

`make verify-plan` shows affected **areas**, application regression depth, and selected
commands. `python3 scripts/verification.py plan --json` also exposes each changed
file's ownership. `make verify` runs that plan. Git governance remains mandatory.

## Ownership and regression depth

Area and depth are independent: an authentication change keeps broad application
regressions without automatically running unrelated editor or discovery tooling.
Plans compose the union of all changed areas, including pinned and dirty child changes.

| Changed area                                                             | Selected checks                                                                                                                                   |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Ordinary Markdown documentation (excluding governance guides)            | UTF-8, whitespace and JSON checks; no runtime dependencies                                                                                        |
| AGENTS/domain/test guides, repository skill Markdown, worklog template, Git hooks                   | Governance/harness fixtures plus text validation                                                                                                  |
| Existing locale string values with identical shape/placeholders/markup   | Text/JSON only                                                                                                                                    |
| Locale key/shape changes                                                 | Broad frontend application checks, unit/UI and production-route tests                                                                             |
| Backend application/tests/migrations/dependencies                        | Independent domain lint/architecture/tests/contracts; shared security/data changes retain complete backend suite                                  |
| Frontend application/auth/API/shared state                               | Application static/type/API/format checks, unit tests; UI/browser and production routes according to depth                                        |
| Contracts                                                                | Consumer baseline/breaking changes: contract/types/app/unit/production routes; parent-verified additive provider-only changes: consumer api-check |
| Docker/deployment                                                        | Env/initializer checks and fake-Docker orchestration tests; no live deployment                                                                    |
| Public discovery tooling                                                 | Discovery fixtures and isolated static build/browser checks; parent IndexNow tools have separate publication checks                               |
| Style studio                                                             | Application regression checks, editor file-access fixtures and editor browser suite                                                               |
| Branding                                                                 | Public identity fixtures, production build/routes; parent adds isolated customized build                                                          |
| Verification harness                                                     | Classifier, scheduler, receipts and governance fixtures                                                                                           |
| Shared build inputs (Makefile/Vite/dependencies/CI) or unknown ownership | All repository areas                                                                                                                              |

The application risk levels remain `none/docs/copy/behavior/ui/full` for existing
consumers. `full` depth means broad application coverage; `VERIFY_FULL=1` means
**all areas**. Root and nested AGENTS guides and `.agents/skills/**/*.md` are governance;
other ordinary Markdown is text only. Executable/config skill files retain the
unknown-path fallback until their impact is explicitly registered. A missing comparison revision expands to all areas. Invalid/deleted
locale data expands application checks; malformed JSON also fails lightweight validation.
Shared CSS retains broad app checks; shared app.css changes additionally select style studio and discovery because both
consume its tokens/styles. Domain-owned CSS uses actual runtime consumers and existing coverage, as described below.
Structural changes to discovery/home.project locale data and editor API/locales select
their actual tool consumers too. Unknown impact within the app retains
broad app suites. No manual skip/downgrade flag is provided.

Existing reviewed billing/admin selections remain supported. Backend domain selection follows the strict #152 policy below; shared auth/security/data regressions remain complete. A new locale key does not imply that browser tests can be skipped.

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

The dated 2026-10-07 benchmark, revision ranges, raw-log references and limitations
are preserved in [worklog 0211](../worklog/0211-scoped-verification-reuse.md).
Those single-run measurements are not current timing guarantees; record new task
scope and observed results in its own worklog.

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
as a wall-time gate. Backend domain selection follows #152 below.

## Independent backend domains and provider additions (#152)

The parent selects static import consumers and existing domain test files, not filenames
alone. Router/service/model names match `tests/api/v1/<domain>/`, optional integration
folders, and `test_<domain>*.py`; no per-feature registry is required. Multiple domains
form a union. Runtime changes retain smoke/OpenAPI checks; test-only changes select the
changed files. A router needs real API/integration coverage, and persistence imports need
owned integration coverage. Missing/deleted/unsafe paths, dynamic/star imports or unknown
ownership broaden. Shared auth/API-key/users/admin/billing, core settings/infrastructure,
ORM/model/migration/shared root fixture changes keep the complete backend suite. Domain-local conftest changes select their actual pytest subtree. Pytest remains sequential.

The narrow entry-point exception only accepts new router imports and constant API-prefix
registrations immediately after existing include_router calls and before mounts/returns.
Other startup, transport, lifecycle or existing route registration edits stay broad. Static
selection is not proof that a new feature's tests cover every behavior: review auth/ownership,
errors and real side effects where applicable. `make backend-test PYTEST_ARGS='tests/...'`
is the existing executable interface; the planner puts its selected paths in the command
and receipt key. Explicit full/CI ignores scoped selection and local receipts.

Provider compatibility allows only new paths/methods/components while every existing
operation/component and global field stays exact. Changes to existing schemas (even optional
fields), inherited parameters/servers, security or removed operations are not assumed safe.
`contract-check` checks export freshness and this pinned-consumer relation; type drift is
checked from the child's own baseline. An unused provider addition does not regenerate or
rewrite the child and does not run frontend UI/build/editor/branding. A frontend adopting
that API still owns a coordinated child baseline/provenance/type/caller PR. Contract checker
implementation changes run its fixtures/provider guard/consumer type check; actual consumer
or breaking contract changes retain broader checks. The parent-only helper modules are not
read by standalone B4React; absent helpers keep legacy broad backend behavior.

Schema rejection belongs at the router/model boundary without DB/signup/login per input.
A representative invalid-after-valid persisted-state test remains. Full-system scenarios
own seeded login/duplicate-email behavior; billing identity adoption uses one seeded principal,
while aggregate scenarios keep their 50-record dataset. Stateless input-free GETs do not need
artificial integration/422/seeded cases or boilerplate comments. See the backend test guide.

The deliberately strict compatibility rule follows the OpenAPI
[Paths/Components model](https://spec.openapis.org/oas/v3.1.0.html); it does not claim to
prove all semantic backward compatibility. Probe first/repeat timings and omitted checks
are recorded in the task worklog, without a timing gate.

## CSS ownership from runtime consumers

CSS-only edits are not shared merely because they live in `app.css`. For each changed
rule, the classifier requires a leading class anchor and finds its runtime consumers
under `src`, `scripts` and `public` (excluding tests/generated outputs). Every consumer
must belong to a registered domain with existing mapped coverage. Home, profile,
support, inbox and prompt-builder follow the same rule as billing/admin; class names
need no domain prefix or per-selector registry. Multiple owners select the union.

A domain-owned class and its descendants, child selectors and ordinary pseudo states
can select that domain's static/unit/browser/build checks. Existing reviewed render-case
selection remains available when all owners qualify. Shared controls, global selectors or
tokens, keyframes, missing consumers/coverage, script/static producers outside mapped
domains, sibling combinators and unsupported selector syntax retain broad checks.
Unknown/shared `app.css` changes also retain editor/discovery checks. `VERIFY_FULL=1`
and CI retain all areas. This policy does not change repository-wide receipt binding;
dependency-specific receipts remain a separate follow-up (#149).

## Literal response cache-header changes

A bounded exception handles existing router edits that change only a literal
`Cache-Control` value in an explicitly imported FastAPI/Starlette response constructor.
The classifier compares complete ASTs after masking that value; imports, authentication,
service calls, response body and every other header must remain identical. Constructor
aliases are accepted only when unshadowed. Dynamic values, dictionary unpacking and
unresolved constructors do not qualify.

This proven transport-only edit does not require a new persistence integration test just
because an unchanged response schema shares a module with ORM entities. It still runs the
domain's existing tests plus common smoke/OpenAPI, architecture, lint and contract checks.
Shared/protected domains, model/DB/migration changes, missing coverage, simultaneous service
persistence changes and explicit full/CI retain their existing broader requirements.
This is not general symbol-level Pydantic/ORM inference: other changes that merely import
response schemas may still conservatively broaden. No fake DB test is added to unlock scope.
