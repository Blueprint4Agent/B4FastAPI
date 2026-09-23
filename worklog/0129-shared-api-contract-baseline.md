# Commit Title

fix(contract): establish shared API contract baseline

# Changed File Scope

- contracts/: OpenAPI snapshot and behavioral contract.
- src/backend/app/: error response composition, OAuth metadata, readiness, SSE schemas, export utility.
- src/backend/tests/: contract, cookie, SSE, refresh/logout regression coverage.
- src/frontend/: generated types, event/readiness type consumers, generation command and guides.
- Makefile, README.md, backend guides, notes/ko/: workflow and synchronized documentation.

# Reason

Prepare a reliable API baseline for a shared React frontend and alternative FastAPI/Spring Boot implementations. Previously, generated contracts omitted dependency errors/readiness and misrepresented SSE transport.

# Impact

- Adds an offline snapshot export and frontend type generation flow.
- Preserves existing error envelopes, refresh token values, cookies, and logout semantics.
- Documents current runtime limitations instead of claiming replay or refresh-token rotation.
- No DB migration or deployment topology change.

# Verification

- make check: passed.
- make test: 70 backend tests and 51 frontend tests passed.
- make contract-check frontend-typecheck: passed.
- git diff --check: passed.
- Existing Pydantic and argon2 deprecation warnings remain.

# Loop Alignment

- Backend request lifecycle: preserved router/dependency/service/error-handler boundaries; shared response declarations describe dependency failures.
- Backend domain event loop: preserved service publication and stream delivery; event schemas now reach generated frontend types.
- Backend background task loop: not applicable; no new queued work or side effects.
- Frontend API state loop: preserved API wrapper/hook/page layering.
- Frontend realtime refresh loop: existing dispatch/state updates retained; reconnect snapshot recovery is documented follow-up work, outside this contract declaration change.
- Desktop connectivity recovery loop: existing readiness polling/recovery lifecycle retained; readiness type now comes from OpenAPI.
- UI composition loop: not applicable; no component, layout, or style changes.
