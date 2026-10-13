# Commit Title

docs: correct harness configuration references

# Changed File Scope

notes/frontend-submodule.md; notes/ko/frontend-submodule.md; src/frontend gitlink; this worklog

# Reason

Align harness references with the current implementation and make the API contract source reproducible.

# Design

Correct layout instructions to runtime APP_LAYOUT and /config.app_layout. Integrate only the child contract provenance correction after its PR merges.

# Verification Plan

Run make verify-plan then make verify against the task base. Check provider/consumer JSON equality. Validate staged commit and actual PR metadata. Parent also validates integrated contracts and packaging.

# Impact

Documentation/provenance only; no runtime, schema, environment, or deployment changes.

# Loop Alignment

Request, domain event, background task, API state, realtime refresh, desktop recovery and UI composition loops are not applicable because no runtime behavior changes.

# Verification

- Child PR https://github.com/Blueprint4Agent/B4React/pull/90 merged with merge commit 175907e8e456f628c179afa80c4ab92b942040c6 after full frontend verification and actual PR governance validation.
- make verify-plan / make verify passed against starting HEAD 509155a: backend=False, frontend=full.
- Passed parent hooks-test, project-brand, frontend-contract-check, frontend-package-verified and project-build-test.
- Reused content-bound child check/test/test-ui/test-routes/test-style-studio receipts; no duplicate expensive child runs.
- Provider source commit and consumer OpenAPI semantic equality passed.
- Backend tests omitted by the classifier because no backend code or schema changed. Runtime loops and extra manual visual checks are not applicable to documentation/provenance-only edits.
- Staged commit metadata and actual PR metadata are validated with repository governance targets.
