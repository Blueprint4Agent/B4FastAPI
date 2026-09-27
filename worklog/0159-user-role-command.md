# Commit Title

feat(auth): add operator role command

# Changed File Scope

Backend role command, Makefile, docs and frontend gitlink

# Reason

Manage roles outside the UI and respect disabled login in profile actions.

# Design

CLI validates role and calls a transactional repository operation; protect the last active admin. No HTTP/schema changes. Pin the separately merged frontend fixes for disabled-login menus and same-email OAuth history duplicates.

# Verification Plan

Run root Make check/test; frontend check/test/build; validate staged Git governance.

# Impact

No new role configuration UI or public API. Existing authentication remains compatible.

# Loop Alignment

CLI is outside HTTP lifecycle; no background tasks or realtime events needed. Backend authorization reads current DB roles. Frontend reuses config state and shared profile composition; connectivity recovery is unchanged.

# Verification

Passed `make check test` on the final code: 80 backend tests and 67 frontend tests. Child `make check test build` and `make test-ui` (46 browser cases) passed. B4React PR #15 passed Git governance/Frontend checks and merged with a merge commit; gitlink pins 64af8da9ca2192de2e44cb67d25feb02c83f1d61 with identical tested contents. SQLite integration covers permission changes using existing tokens, last-admin protection and invalid users/roles. PostgreSQL table-lock behavior was not exercised locally (no isolated PostgreSQL harness in this task). No required Make checks skipped; no real account roles changed.
