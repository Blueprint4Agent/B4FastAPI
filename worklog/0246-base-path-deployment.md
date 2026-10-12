# Commit Title

feat(deploy): support configurable monolithic base paths

# Changed File Scope

FastAPI settings/static serving/cookies, Docker build/preflight/smoke, generic Nginx fragment, deployment test harness, English/Korean deployment docs and B4React gitlink (merged PR #83).

# Reason

Allow independently deployed apps beneath configurable URL prefixes without hardcoded product names.

# Design

Default root remains compatible. Docker APP_BASE_PATH supplies frontend VITE_BASE_PATH and FastAPI root_path. Proxy strips prefix; application URLs retain it. Isolate browser storage and cookies by canonical path. Package a build-path manifest and reject runtime mismatches.

# Verification Plan

Run focused prefix/root routing, assets, OAuth URL and session isolation tests; production monolithic HTTP/browser checks behind Nginx; make verify-plan then make verify and Git governance.

# Impact

Path changes require a frontend rebuild and new login. No migrations or new external providers.

# Loop Alignment

Existing API/auth/realtime/desktop recovery owners remain intact; only URL construction and persistence namespace change. No new domain mutations/events/background tasks. UI composition stays unchanged.

# Verification

make verify-plan selected backend plus full frontend scope. make verify passed: backend architecture/env/lint, 490 backend tests, unchanged OpenAPI contract, frontend checks (171 tests, 214 UI cases, 10 production route and 11 public discovery cases, 3 Style Studio cases), parent contract/packaging and isolated custom-brand build. Matching child receipts were reused; backend checks were rerun after final source edits. make base-path-deployment-test passed using two disposable FastAPI/React Docker images behind real Nginx: nested/direct routes, reload, public assets, API 404s, private-route blocking, SSE and independent refresh/logout/storage. Runtime/build mismatch and prefix-aware internal smoke have regressions. External mail/OAuth/Stripe, public DNS/TLS and native desktop packaging were omitted because no live deployment or provider setup was requested. Child PR #83 merged as adb69ca7f538fcb240c771414f2e6c738698aef8.
