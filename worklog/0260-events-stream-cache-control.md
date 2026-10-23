# Commit Title

fix(events): prevent caching authenticated event streams

# Changed File Scope

src/backend/app/routers/v1/events.py, existing events API test, EN/KO API authentication notes and this worklog.

# Reason

Run a real small API maintenance task after documentation publication: authenticated SSE responses currently say no-cache, which permits storage with revalidation; explicitly use no-store for per-user event payloads.

# Design

Change only the successful SSE transport Cache-Control header. Preserve Router -> RealtimeService delegation, session dependency, framing, retry/replay semantics and OpenAPI schema. Extend the existing API transport assertion without a DB fixture.

# Verification Plan

Confirm the new API assertion fails against current no-cache, then change the header. Run root make verify-plan and make verify without scope overrides; measure first run and identical repeat, recording any conservative fallback. User now authorized publication: keep this API change in its own commit, then publish the classifier improvement in the same ready task PR.

# Impact

Runtime SSE response header only; no model, DB, frontend, dependency or OpenAPI baseline change.

# Loop Alignment

Request lifecycle still resolves current user and delegates to RealtimeService. Domain event delivery remains unchanged; no state mutation or background task is added. Frontend loops are unchanged because no consumer code changes.

# Verification

- Regression confirmed first: the existing events API test with the new no-store assertion fails against the original no-cache header. Changing only that response header passes the test; authentication and connected event framing remain asserted.
- Root make verify-plan selected the backend-only conservative fallback. AST selection returned None at scripts/verification_backend.py:360: domain events is marked needs_integration because its imported UserResponse lives in app.models.user alongside ORM entities; only tests/api/v1/events/test_events_api.py exists for events. This header-only change does not actually add persistence semantics, so the fallback exposes a remaining module-level overclassification. No classifier change or artificial DB integration fixture was added to hide it.
- First automatic make verify: measured process wall 73.446 s, backend 500 passed / 17 existing warnings in 68.29 s. Lint/format, architecture, env/project fixtures, provider compatibility and OpenAPI export checks passed. No frontend UI/browser/build selected. Log: /tmp/b4-api-cache-first.log, raw run-1lnjt840.
- Explicit requested API timing: make backend-test PYTEST_ARGS=tests/api/v1/events/test_events_api.py passed 2 tests in 0.53 s; complete Make process 1.606 s. This is a separate API-only timing sample, not the automatic pipeline time or a replacement for its selected checks.
- Identical automatic repeat: measured process wall 0.787 s (runner 0.3 s), reusing the successful backend command receipt; /tmp/b4-api-cache-repeat.log and run-4tbbn890. No first-run result reuse was used above. Timings are local single observations, not universal API upper bounds.
- English/Korean authentication notes record the runtime header. The provider baseline is unchanged. Documentation work was separately committed/pushed/merged via B4React #99 then B4FastAPI #157 before this branch. Initially kept local for measurement; user subsequently authorized commit/push/merge. Publish this runtime change separately from the classifier commit, retain the measured validation evidence, and rerun the API after merge.
