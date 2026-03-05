# chore: set up alembic migration baseline

- scope: backend
- changed files:
  - backend/pyproject.toml
  - backend/uv.lock
  - backend/alembic.ini
  - backend/alembic/env.py
  - backend/alembic/script.py.mako
  - backend/alembic/versions/0001_initial_auth_schema.py
- brief reason and impact:
  - Introduced Alembic as the schema migration system to replace ad-hoc create_all schema bootstrapping.
  - Added async-aware Alembic environment using project settings so `.env` DATABASE_URL is used consistently.
  - Added initial baseline migration for current auth tables to allow forward schema evolution and safe revision history.
