# Commit Title

feat(admin): integrate administrator user panel

# Changed File Scope

Frontend gitlink, README translations and this worklog.

# Reason

Expose the administrator-only user directory from the profile menu in a settings-style workspace.

# Design

Adopt the separately reviewed B4React panel and its immutable provider snapshot. The panel reuses the app sidebar and shared controls, with read-only filters and pagination. Ordinary users cannot mount the directory; backend admin dependency is authoritative. No role editing interface.

# Verification Plan

Run root make check test build, child check test build and browser test-ui. Verify child merges before pinning; stage and validate Git governance.

# Impact

Adds /admin and an admin-only profile link, including bootstrap administrators. Shows identity, role, enabled/verified state, providers, signup and latest successful login. No online-presence or full-login-history claim.

# Loop Alignment

Backend request lifecycle follows router/dependency/service/repository. Read-only API needs no new events/background tasks. Frontend uses generated auth API and an owner-scoped hook, focus/manual refresh and desktop offline/recovery. Existing UI composition and sidebar resizing are reused.

# Verification

Passed root `make check test build` (82 backend and 73 frontend tests), child `make check test build`, and `make test-ui` (50 browser cases). Mobile/desktop screenshots reviewed. B4React PR #16 passed Git governance/Frontend checks and merged with merge commit f7f50b884c18e518eb1c36a99d7b5a8b9ae94489; its tree matches the tested child commit. The earlier provider-only contract deferral is resolved by this pin. No required checks skipped and no operational users modified.
