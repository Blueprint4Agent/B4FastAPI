# Commit Title

feat(auth): store profile photos through object storage

# Changed File Scope

Backend auth photo transport/service/repository, users photo reference migration, image codec, contracts, tests, docs and merged frontend gitlink.

# Reason

Connect the storage foundation to profile editing without embedded Base64 uploads and preserve account state when external storage fails.

# Design

Authenticated bounded binary upload/read/delete on /auth/me/photo. Decode/resize/strip metadata in domain service; store unique immutable WebP keys and location fingerprint in nullable JSON. User response keeps a versioned API photo URL. Frontend fetches private bytes with bearer auth and owns one object URL in AuthProvider. Compare-and-swap profile URL prevents stale replacements; upload first, commit reference, clean old object after success. Compensate failed DB updates only after confirming the new key is not current. Cleanup failure logs an orphan reference without claiming rollback. Account deletion returns the managed reference for cleanup. Legacy photo rows remain readable; PATCH photo writes are retired. No automatic remote-to-local fallback, worker sync or dual writes.

# Verification Plan

Auth contract/ownership, real temporary DB+local storage upload/read/replace/delete, invalid/oversized images, storage/DB failure and concurrency tests; migration upgrade/downgrade; child API/state/browser failure and reload scenarios. Root verify-plan/verify and governance; child merge before parent gitlink.

# Impact

Migration adds nullable users.profile_photo. Coordinated client contract update required for photo edits. Existing names/shortcuts unaffected. Private reads are no-store; profile photo failure never logs out a session. No real cloud test uploads or user photo modifications.

# Loop Alignment

Router streaming -> photo service -> image/storage/repository. No realtime publication (existing auth mutation/reload/desktop recovery owns refresh); no background synchronization or automatic fallback. Cleanup is bounded best effort, residual orphans require operator action.

# Verification

Full backend/frontend scope selected by make verify-plan. Root make verify passed: hooks, initializer/architecture/environment checks, Ruff, 346 backend tests, OpenAPI export and pinned contract checks, branding, frontend packaging and project build tests. Child PR #64 merged as 2ddb51f; matching child receipts reused (147 tests, 165 UI, 9 production routes, 3 style-studio). No selected checks omitted. Existing Python 3.13 interpreter exits 137 even for -V; validation used separately installed Python 3.13.13 with UV_PYTHON and UV_PROJECT_ENVIRONMENT, without changing the existing interpreter or user environment. Tests used temporary DB/local storage and mocked browser transport; no live cloud object writes or account photo modifications. No new event/background/realtime loop: existing auth mutation and refresh remain authoritative, cleanup is best effort with manual orphan reconciliation.
