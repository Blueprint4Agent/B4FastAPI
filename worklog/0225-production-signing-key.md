# Commit Title

fix(auth): reject unsafe production signing keys

# Changed File Scope

Settings, configuration tests, project initializer, env examples and EN/KO runtime documentation.

# Reason

Production accepts empty and public example signing keys; project initialization also preserves the current example placeholder.

# Design

Fail before startup I/O for blank, placeholder or short production signing keys. Require the HMAC digest size (32/48/64 UTF-8 bytes for HS256/384/512). Preserve development compatibility and existing configured keys. Generate a random key when initializing either published placeholder. No API contract or schema changes.

# Verification Plan

Root make verify-plan and make verify across the branch; regression tests for production/development boundaries and initialization. Use TERM=xterm-256color for the existing terminal-dependent test, documenting this environment limitation.

# Impact

Production deployments using unsafe keys must configure a unique random key before restarting. Changing an existing key invalidates tokens and key-derived credentials; do not rotate working deployments automatically.

# Loop Alignment

Validation runs before request lifecycle begins. No router, domain event, background task or frontend loop changes apply.

# Verification

- Root make verify-plan selected backend + full frontend because environment/tooling changed; make verify passed.
- Backend: 446 tests passed. Frontend: 147 unit/integration, 188 UI, 9 route and 3 style-studio tests passed; branding, contracts and packaging passed.
- TERM=xterm-256color was supplied for the pre-existing terminal-dependent fixture; the default TERM=dumb failure is separately tracked by the readiness audit.
- No live payment/email or production credential rotation was performed. Existing successful checks are reused only through content-bound receipts.
