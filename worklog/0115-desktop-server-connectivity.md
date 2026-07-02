# Commit Title

`feat(frontend): add desktop server connectivity`

# Changed File Scope

- `src/frontend/src/api/system/` and `src/frontend/src/hooks/api/system/`
- `src/frontend/src/hooks/connectivity/`
- `src/frontend/src/components/layout/ConnectivityBanner.tsx`
- Frontend auth, configuration, realtime subscription, bootstrap, locale, and style files
- Frontend connectivity unit and integration tests
- Backend and Docker environment examples for the packaged macOS Tauri origin
- English and Korean frontend engineering, usage, and test documentation

# Reason

The packaged desktop application needs to distinguish server readiness from browser network hints,
report outages, and recover cleanly when FastAPI becomes available again. The packaged macOS origin
also needs an explicit backend CORS example so readiness and authenticated API requests are accepted.

# Impact

- Tauri checks `/health/ready` at startup and periodically while browser builds remain unchanged.
- Failed checks use timeout, exponential backoff, jitter, and a manual retry action.
- Authentication, app configuration, and realtime subscriptions recover after connectivity returns.
- Packaged macOS clients can be allowed through `tauri://localhost` in backend CORS configuration.
- Offline mutation queues, conflict resolution, and offline data synchronization remain out of scope.

# Verification

- `make check`
- `make test`
- `make frontend-build`
- `make frontend-desktop-build`
