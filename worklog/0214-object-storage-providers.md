# Commit Title

feat(storage): add configurable local and S3 object providers

# Changed File Scope

Backend core object storage, centralized settings, application lifespan/DI, dependency lock, tests, environment examples, Docker volumes, English/Korean documentation.

# Reason

Issue #108 requires a reusable storage boundary selected by environment instead of tying domains to Base64 or a vendor SDK.

# Design

Provide a typed async ObjectStorage interface, immutable metadata and normalized errors. Local and S3 implementations share bounded bytes put/get/stat and idempotent delete. Select local/s3/r2/supabase via centralized settings as requested; the three remote selections share S3 I/O with provider-specific defaults and validation. Update .env.example only, preserving real .env values. Private by default with no public mount or upload endpoint. Lifecycle owns one client per application and DI provides it. Blocking I/O runs in a worker thread. Local uses atomic single-file records for bytes plus metadata, hashed key filenames and no-follow reads under an operator-owned root. Provider switching does not migrate data. No profile/DB/API contract changes. Follow-up request: startup must probe local write/read/delete or remote HeadBucket, log safe success/failure evidence, abort on failure and close resources. HeadBucket does not establish object write permissions.

# Verification Plan

Temporary-directory local contracts/path safety/concurrent writes; stubbed S3 requests/errors/stream close; settings/factory and lifespan/DI checks. Root make verify-plan then make verify, staged governance, actual PR metadata check. Do not contact real cloud accounts.

# Impact

Default local provider adds a persistent data directory when app starts. S3 must be explicitly configured; no fallback or auto-created bucket. New boto3 dependency. Existing profile Base64 remains until a separate domain integration. No migration.

# Loop Alignment

Core infrastructure only: DI supports existing router/service/data flow. No new domain mutation or realtime event. Background tasks are not applicable; bounded file I/O completes in request-driven calls with thread offloading. Frontend loops do not change.

# Verification

Root make verify-plan selected backend plus full frontend/integration (settings/dependency/Docker changes); make verify passed. Backend: 329 tests including 38 storage regressions. Frontend: 143 unit/component cases, 164 UI cases, 9 production routes and 3 style-studio cases. Architecture, formatting, environment-key contract, API contracts, packaging, hook and project-build harnesses passed. Docker Compose config --quiet passed using the example environment. Separate fresh Python processes confirmed local/s3/r2/supabase selection and rejected unknown provider values. Examples were updated without changing deployment secrets. During user-reported not_found diagnosis, corrected only the R2 endpoint in the ignored backend .env: its URL incorrectly included the bucket, which the SDK appended again. Credentials and bucket were preserved. Live HeadBucket, server startup success logs and /ping confirmed recovery.

Final startup probe/logging and actionable R2 endpoint validation passed root make verify; unchanged frontend checks reused matching receipts. No selected checks are intentionally omitted. Live R2 HeadBucket passed on the configured bucket during diagnosis; no remote objects were written/deleted. AWS/Supabase live checks and remote CRUD remain unrun; SDK Stubber coverage is not live connectivity evidence. Domain events/background tasks and frontend loops are not applicable for this infrastructure-only change; no public file endpoint or profile migration is included.
