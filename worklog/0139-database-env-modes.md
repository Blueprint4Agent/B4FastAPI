# Commit Title

docs(env): clarify database names when switching drivers

# Changed File Scope

- src/backend/.env.example and docker/.env.example
- README.md and notes/ko/README.md
- worklog/0139-database-env-modes.md

# Reason

Switching the development driver to PostgreSQL while retaining SQLite's template.db
file name caused a database-not-found startup error.

# Impact

Document SQLite file names versus PostgreSQL database names, host versus container
addresses, and the need to change DB_DRIVER and DB_NAME together. Explain that env
sync preserves values and checks do not verify database existence. Example defaults
and application behavior remain unchanged. Local env and backups are excluded.

# Loop Alignment

Backend lifecycle, domain events, background tasks, and frontend API state, realtime
refresh, desktop recovery, and UI composition loops are not applicable: only example
comments and documentation change.

# Verification

- make check passed, including environment contract, lint/format, type, and API checks.
- git diff --check passed.
- Local tests not rerun, following the user's preceding test-skip instruction;
  this commit changes only documentation and example comments.
- Existing GitHub CI remains enabled.
