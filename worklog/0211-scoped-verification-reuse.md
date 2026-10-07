# Commit Title

perf(verification): reuse scoped checks across integration

# Changed File Scope

Verification runner/cache, Make targets, regression fixtures and localized verification guides.

# Reason

Avoid repeating unchanged checks across local validation, hooks and frontend integration. Evaluate affected domains instead of always running all frontend tests.

# Design

Measure the previous billing/admin change before edits. Diagnose receipt mismatches without exposing environment secrets; normalize equivalent execution contexts while retaining real tool/config invalidation. Select explicit affected frontend suites with conservative fallback for shared/protected/unknown changes. Keep contracts, packaging, governance and full verification available. Record comparable before/after timings.

# Verification Plan

Real Git/cache/planner regression tests, baseline and improved benchmark for the same revisions, then mandatory full verification for harness changes and actual push/PR governance.

# Impact

Local verification workflow only. No application or database changes.

# Loop Alignment

Application API, realtime, desktop and UI loops are unchanged; this change owns build/test orchestration.

# State Ownership

Local Git-directory receipts own short-lived evidence; no application state changes.

# Memoization

React memoization is not applicable to Python verification tooling.

# Performance Evidence

Measured locally on the previous billing/admin UI change (child ca3f83f..57a67d5, parent 06e55ba..7c4922e), with /usr/bin/time -p and production application files unchanged. Before: child 121.01s (check+test 37.0s, UI 77.9s, build 5.5s); redundant parent 122.36s. After scope/cache changes: first child 101.16s (check 28.1s, 39 related tests 2.4s, 67 UI tests 64.9s, build 4.9s); identical child rerun 0.85s; parent integration 1.37s with all child receipts reused and contracts/packaging still executed. Single-run wall times, not statistical latency claims. Earlier child login shell selected Python 3.9 while parent selected 3.14; follow-up execution is standardized through root make -C/git -C commands. Real toolchain differences remain valid cache misses.

Raw local evidence: /tmp/b4-verify-baseline-first.log, /tmp/b4-verify-baseline-integration.log, /tmp/b4-verify-improved-first.log, /tmp/b4-verify-improved-repeat.log, /tmp/b4-verify-improved-integration.log. This benchmark deliberately selects the already-merged UI revision range; the harness implementation itself separately receives full branch verification.

# Verification

Root make verify-plan selected full backend/frontend verification for the harness changes. make verify passed: 280 backend tests, 140 frontend tests, 164 browser UI cases, 9 production routes, 3 style-studio cases, architecture/type/format/contracts, packaging and project build. Dedicated scope/cache fixtures passed, including real hook PATH normalization and subset isolation. No selected checks omitted. Frontend loops are unchanged because only verification orchestration changed.

## Refined UI benchmark

After requested component-level refinement: the same UI revision range passed in 30.72s (check-affected 9.3s; 39 related unit/integration cases 2.2s; 32 reviewed browser cases 13.2s; build 4.9s). Browser cases use isolated fully-parallel scheduling at the existing worker limit. Global types and static architecture/UI/state rules remain; unchanged tooling self-tests run only for broad/full impact. This supersedes the initial 101.16s domain-only benchmark. Raw evidence: /tmp/b4-verify-refined-first.log, /tmp/b4-verify-refined-repeat.log, /tmp/b4-verify-refined-integration.log. Scope/cache/render-selection fixtures: 28 passed. Final full verification reruns after this refinement.

Final refined full verification passed all selected backend/frontend, routes, style-studio, contracts and project-build checks. Final warm timings: identical child 1.08s, parent integration 1.65s. English/Korean verification guides include the scenario table and distinguish measured values from estimates.

Actual pre-push diagnosis also found Git exporting its default GIT_EXEC_PATH. Normalize the absent/default value identically, and cover the real exported hook environment in the receipt regression. Non-default helper/toolchain changes still invalidate proof.

Merged child PR Blueprint4Agent/B4React#62 (4c327be). Actual pre-push full verification succeeded; subsequent root-shell child full verify reused all six command receipts in 1.05s (/tmp/b4-actual-hook-repeat.log), covering the real Git-exported environment.
