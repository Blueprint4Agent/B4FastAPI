# refactor: migrate auth record schema to multi-provider identities

- scope: backend
- changed files:
  - `backend/app/models/user.py`
  - `backend/alembic/versions/0002_auth_identities_multi_provider.py`
  - `backend/app/services/auth.py`
- reason:
  - replace single-provider `auth_records` model with a multi-provider identity model to support upcoming OAuth providers.
- impact:
  - users can now hold multiple auth identities (per provider constraints enforced by DB unique keys).
  - existing email/password login behavior remains compatible while identity storage moves to `auth_identities`.
