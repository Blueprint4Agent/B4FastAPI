# Commit Title

perf(verification): scope backend domains and preserve additive contracts

# Changed File Scope

Parent-only dependency-free backend/contract selection helpers and fixtures, shared verification planner/ownership policy, provider contract wrapper, backend validation/seed fixtures and EN/KO guides; child synchronizes shared planner without reading its parent.

# Reason

B4FastAPI #152: independent APIs should select real domain coverage without all backend/frontend tests; schema failures should not construct a real database.

# Design

Use static Python import consumers plus conventional domain test paths, retain smoke/OpenAPI boundaries, and broaden protected auth/DB/migration/config/dynamic/unknown changes. Allow only additive paths/operations/components with every pinned existing contract fragment unchanged. Use existing Make backend-test PYTEST_ARGS instead of another harness target. Child is independent; parent-only helper absence retains broad backend behavior.

# Verification Plan

Real Git fixture plans for stateless/new DB/old domain/shared changes and additive/breaking contracts; focused moved validation/invariant checks; final root Make checks; temporary independent GET API probe first/repeat timings with exact restoration; governance and child-first PR integration.

# Impact

No application runtime change. Provider additions need not rewrite the pinned child contract/types until a frontend consumer adopts them. Auth/ownership/data gates remain; no skip flag or time gate.

# Loop Alignment

Runtime request/event/background and frontend state/realtime/desktop/composition loops are unchanged. Domain tests retain persistence/ownership assertions; probe wiring is temporary and restored.

# Verification

- Static backend/contract fixtures passed: 6 Git-layout/selection cases cover new/existing/stateless/persistence/shared/dynamic/missing/unsafe/local-fixture conditions and registration placement; 2 contract tests cover additive and breaking/security/schema/boolean-vs-number changes. Root harness totals 49 verification + 8 Git-hook cases, child 63.
- Focused moved-validation/seed/scenario checks: 54 passed in 5.04 s. All 10 keyboard schema inputs now run at the API boundary without DB/signup/login, service invocation is explicitly rejected, anonymous PATCH remains 401, and one invalid-after-valid persisted-binding invariant stays integration-owned.
- Seeded login/duplicate-email owners are full-system scenarios, retained by protected auth changes. The billing existing-principal fixture seeds one user; aggregate scenarios retain primary+50.
- Complete affected root make verify-plan / make verify passed: 500 backend tests (17 warnings) in 53.04 s; runner 56.4 s with 4 commands. Shared root fixture changes intentionally retained the entire backend suite. Frontend runtime/build/browser tests were omitted as unchanged; child harness and pinned consumer api-check ran instead (run-7vvk20jk).
- Child B4React #97 merged at 051fac79ece82e1d73e3cdcc90ae72ef59a2753c; tested tree 87c074c is identical. No frontend contract/generated type or runtime behavior changed.
- New domain selection uses existing backend-test PYTEST_ARGS; no extra Make target, registration table, skip flag or timing gate was added. Only strict constant appended API router wiring can narrow main.py; static mounts/returns and prior routes stay protected.
- Temporary public GET probe used a Pydantic response/service/router and one actual-app HTTP test; no artificial 401/422/DB/duplicate unit test. Its appended router and generated provider baseline were checked. First root verification: 6.49 s, 2 fresh commands, 22 pytest cases (new API + common smoke/OpenAPI), backend lint/architecture/export/compatibility and pinned consumer api-check. Consumer type proof alone was invalidated before the first sample to ensure both commands were fresh.
- Same-input root verification: 0.45 s, both commands reused. The API is owned directly by the parent, so first root verification is its parent integration step; no child API adoption/extra integration ritual is needed for an unused provider addition.
- The previous selector's plan on the same probe selected the full backend bundle plus frontend check/unit/production/build/package checks; this was compared as a plan only, not rerun as a claimed timing baseline.
- All temporary API/model/service/router/test sources, main.py wiring and provider JSON were restored exactly; Git tree was clean afterward. Branch verification after restoration reused all 4 matching proofs in 0.5 s (run-27ijkaxe); no application/API/consumer snapshot change remains.
- 30 s soft target is met for this single local stateless API sample. Shared auth/ORM/migrations/unresolved effects still widen; no claim that all DB/schema/security changes finish within 30 s. Total agent/coding/PR time and token savings were not measured. Worklog/guide ceremony remains #151.
