# Commit Title

refactor(verification): separate areas and parallelize isolated checks

# Changed File Scope

scripts/verification.py, scripts/verification_areas.py, scripts/verification_runner.py, runner/classifier regression tests, Makefile, notes/verification.md, notes/ko/verification.md; parent integration pins the merged child; src/backend/TEST.md documents test-only tracing isolation.

# Reason

Issue B4FastAPI #148: unrelated tooling suites inflate small changes; full checks serialize independent backend/frontend work.

# Design

Separate affected areas from frontend risk level. Compose explicitly owned checks; unknown/shared changes widen. Keep frontend output writers/browser ports ordered; run isolated backend work concurrently with frontend. Bound concurrency and preserve failure propagation, per-command logs and receipts. No application runtime or API contract changes.

# Verification Plan

Git fixture classification and actual runner scheduling/failure tests; root make verify-plan then make verify; compare full serial/parallel runs with identical coverage and no receipt reuse; child-first PR integration and governance.

# Impact

Verification selection/execution only. Preserve security/data backend suite, application checks and explicit full coverage. Do not narrow API domains or expand page ownership in this issue (#152/#94 follow separately).

# Loop Alignment

Backend request/event/task and frontend API/realtime/desktop/UI loops are not changed: this task only changes local verification orchestration.

# Verification

- Selected scope: all areas because Makefile/shared verification inputs changed; no application/security suite was omitted. Root Make targets delegated child checks without a separate check/test/ci ritual.
- Same application coverage in three full-scope observations: backend 502, Vitest 209, app browser 250, production routes 15, discovery 11 and editor 3; isolated custom-branding and tool fixtures also passed. No app tests were deleted.
- Serial commands (VERIFY_FULL=1 VERIFY_JOBS=1 make verify): 249.88 s, 15 commands, zero reused.
- Parallel commands (VERIFY_JOBS=2 make verify; automatically all areas): 219.28 s, 15 commands, zero reused; about 12.2% lower wall time in this sample.
- Trial browser workers=4: 226.44 s; not adopted because wall time did not improve. Final config retains the existing worker limit and enables independent-case scheduling.
- Measurements are single local samples. Classifier fixtures/shared-input handling were refined between runs; application source/test inventory stayed fixed. This is not a strict single-variable benchmark or a timing guarantee. Backend individual duration increased under contention.
- Final classifier/runner coverage: parent 40 verification fixtures + 8 hook fixtures; child 62 Python fixtures. Actual process tests cover overlap, ordered frontend writers, packaging dependencies, failure draining and sequential fallback. Relevant changed Python files pass Ruff.
- Nine real Git fixture before/after plans: contracts/README 10->0 commands; AGENTS 10->1; Compose 10->1; auth/locale shape changes preserve app coverage without unrelated tools; unknown/shared paths retain all areas. Shared CSS, discovery locale structures and editor API ownership have dedicated regressions.
- Evidence: .git/verification-logs/run-q310fnc5 (serial), run-9zz95x6f (parallel), run-vix3nv98 (worker trial); final verification log below. Local full logs/plan JSON are also preserved in Documents/blueprint4agent-verification-review-2026-10-16/implementation-148/.
- Backend pytest remains sequential. Live Docker deployment/browser deployment test, image publication and manual Actions were not run: this is local verification orchestration, not a deployment change.
- Follow-ups: B4React #94 (page selection), B4FastAPI #152 (backend domain selection), #149 (dependency-scoped receipts), #150/#151 (remaining ceremony/repetition). UI 20 s / API 30 s targets are not claimed achieved.
- Final validation/integration: root make verify passed with all areas selected (run-721o3z1a): 63.6 s with 4 unchanged child commands reused; this is not a cold full-run timing. Backend 502 passed after test-only tracing isolation; targeted fake-Docker mail tests 9 passed. B4React PR #95 merged with merge commit 9cce8f8c8c5e6db21fb491708afe7b0155aef292; its tree equals tested commit 8930935. Parent make verify-plan / make verify passed against the merged pin in 1.9 s (run-bfzotb8w): 14 matching commands reused; contract/package validation reran locally. Planned staged governance and actual PR checks are required before merge..
- A later validation exposed an existing developer-environment leak: TRACING_ENABLED=true started native gRPC exporter threads. One fake-Docker subprocess died with SIGTRAP (-5); the macOS crash report states multithreaded fork/pre-exec libdispatch recursion. No assertion was relaxed. Root pytest Make targets now disable real tracing for tests only; runtime .env stays unchanged. Evidence: run-mrb5uepk/2.log. An isolated rerun and complete verification must pass before publication.
