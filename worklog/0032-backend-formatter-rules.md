commit title: chore: apply backend formatter rules
scope: backend
changed files:
- backend/app/main.py
- backend/app/models/user.py
- backend/alembic/versions/0002_auth_identities_multi_provider.py
reason and impact:
- Re-applied backend code formatting across app and migration files.
- Normalized multiline-call and SQL string layout to formatter output.
- Kept backend code style consistent for future save-time formatting.
