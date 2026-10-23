# Commit Title

perf(verification): scope constant response header edits

# Changed File Scope

Parent backend classifier and fixtures, English/Korean verification notes; retain the separately committed events API header change from worklog/0260 for real measurement.

# Reason

A one-line SSE Cache-Control change selected all 500 backend tests because the imported UserResponse shares a module with ORM entities and events has no persistence integration test.

# Design

Add a bounded AST equivalence guard for constant Cache-Control values inside explicitly imported FastAPI/Starlette response constructors. Only byte-independent AST-equivalent transport header edits can bypass the false persistence-coverage requirement; all other source semantics, protected domains/models/shared dependencies and explicit-full fallback remain. No general Python/Pydantic type inference or skip flag.

# Verification Plan

Positive/negative Git fixtures for constructor aliases, literals, auth/service/body/DB edits, mixed changes, protected domains and forced full. Re-run the same existing events API probe through root verify-plan/verify, recording fresh backend command plus harness fixture timings and identical repeat. User now authorized commit/push/merge. Keep API and classifier changes in separate matching-worklog commits, validate the full branch and actual PR metadata, merge with a merge commit, then rerun the API.

# Impact

Narrow current response-header-only false positives without claiming all response-schema imports are persistence-free. The separate API/docs change is preserved in this task branch.

# Loop Alignment

Verification tooling only; runtime loops for the retained events probe follow worklog/0260. No request/service/data/event/background behavior is changed by the classifier.

# Verification

- Root make verify-plan now selects the events API file plus common smoke/OpenAPI (23 tests), architecture/lint/contract checks, and a separate harness regression command for this classifier change. No frontend/app build or all-backend target is selected.
- Final make verify passed: measured process wall 15.406 s (runner 15.0 s), both commands freshly executed and overlapped. Backend bundle 9.1 s, harness 14.7 s; raw run-jkcbo8ot. The earlier same API change used the entire backend 500-test bundle in 73.446 s. This local workflow observation is 79.0% shorter and includes the new classifier safety checks; it is not a repeated controlled benchmark or universal API timing guarantee.
- Identical repeat passed in 0.787 s with both command receipts reused; /tmp/b4-api-scope-repeat.log. The expensive first-run values above do not use receipts.
- Safety fixtures cover imported constructor aliases, literal-only AST equivalence, auth/service/body/other-header edits, dynamic/unpacked headers, shadowed/unknown constructors, actual protected auth router changes, model changes, simultaneous persistence service edits with/without owned integration, and forced-full selection. Static lint/format passed for modified Python helpers/tests.
- The previous runtime API change and its worklog are preserved in a separate commit. This change is parent-local verification logic with EN/KO policy notes. No child source/runtime changes or deployment are included. User subsequently authorized parent commit/push/PR/merge; validate existing proofs and governance, then rerun the API on the merged code. General response-schema symbol inference and non-Cache-Control transport changes remain conservative.
