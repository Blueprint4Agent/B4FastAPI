# Commit Title

refactor(frontend): extract B4React into a pinned submodule

# Changed File Scope

src/frontend gitlink, .gitmodules, root Make/scripts, Docker context and build,
build/desktop CI, English/Korean integration and contract documentation.

# Reason

Allow B4FastAPI and a future B4SpringBoot provider to share independent B4React source.

# Impact

Preserve frontend history in B4React. Parent owns static packaging and pins a reviewed
frontend commit. Clone/init and CI retrieve that pin. Consumer contracts are local;
parent checks semantic schema equality and generated type freshness.
Existing ignored frontend artifacts are backed up before replacing the checkout.

# Verification

- `make check test build` passed: backend 70 tests and frontend 51 tests.
- `make docker-build` passed with Node.js 24 and integrated static assets.
- Contract equality accepts differently formatted JSON and rejects a changed version,
  exercised through `make frontend-contract-check` with a temporary fixture.
- B4React independent `make check test build` and GitHub CI passed.
- `make frontend-package` passed after script formatting.
- Fresh recursive clone fetched the public pinned child commit; Make install, contract,
  generated-type, TypeScript, and integrated packaging hooks passed without local caches.
- Native desktop packages and browser E2E were not run; runtime code is unchanged.

# Loop Alignment

Request lifecycle, domain event, and background task loops remain unchanged.
API state, realtime refresh, desktop recovery, and UI composition loops remain unchanged.
No runtime loop changes are needed for source extraction; existing SSE limitations remain.
