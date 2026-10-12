# Commit Title

fix(deployment): resolve public base path at runtime

# Changed File Scope

Runtime base path configuration, packaged HTML, build/deployment harness and English/Korean documentation. Integrates B4React PR #84 at 97bfab2570abf762ef543cd7615a6eea8cfd59fc after its merge.

# Reason

Reuse one monolithic image at multiple public paths without rebuilding.

# Design

Build relative assets; inject a public base element and metadata before scripts execute. Preserve immutable JS/CSS and existing API, session and routing ownership. No database migration.

# Verification Plan

Run focused path tests and the same-image Nginx browser scenario, then make verify-plan and make verify.

# Impact

APP_BASE_PATH and APP_BASE_URL become runtime settings. Existing fixed-path artifacts remain validated. Restart/recreate is required; route changes isolate browser sessions.

# Loop Alignment

Request/static serving remains infrastructure-owned. Existing API, SSE, recovery and UI loops remain intact. No domain mutation or background task is introduced.

# Verification

make verify-plan selected backend plus full frontend due shared configuration/deployment changes. make verify passed: backend architecture/environment/contracts and 495 tests; delegated frontend check, 172 unit tests, 214 UI cases, 10 production-route cases, 11 discovery cases and 3 Style Studio cases; packaging and custom-project build checks. make base-path-deployment-test passed using one image ID at /qa/nested and /another-app, identical entry bundles, real Nginx navigation/reload, login/refresh/logout, SSE, independent cookies/storage and runtime discovery URLs. Root/nested runtime HTML, HEAD/cache semantics, legacy compatibility, immutable files and static anchors have unit coverage. No required checks omitted; unchanged child checks reused through receipts. Domain event/background loops are not applicable because this is startup/static transport configuration. Actual external infrastructure and native desktop builds are outside this task.
