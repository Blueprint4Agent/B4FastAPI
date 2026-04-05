# chore: consolidate backend linting and formatting on ruff

- scope: backend
- changed files:
  - backend/pyproject.toml
  - backend/uv.lock
  - backend/.flake8 (deleted)
  - backend/app/core/mail_templates.py
  - backend/alembic/versions/0002_auth_identities_multi_provider.py
  - backend/alembic/versions/0003_users_profile_image_url.py
  - backend/app/models/user.py
- reason and impact:
  - removed legacy Flake8 config and standardized lint/format flow on Ruff.
  - added Ruff as a backend dev dependency so `uv run ruff ...` works consistently.
  - kept migration/model files Ruff-formatted to reduce style noise in future diffs.