# feat: add backend api key domain and protected endpoints

- scope: backend
- changed files:
  - backend/app/models/api_key.py
  - backend/app/services/api_key.py
  - backend/app/routers/v1/api_key.py
  - backend/app/core/error/api_key_exception.py
  - backend/app/core/error/__init__.py
  - backend/app/models/user.py
  - backend/app/main.py
  - backend/alembic/env.py
  - backend/alembic/versions/0004_api_keys_table.py
  - backend/app/services/auth.py
- reason and impact:
  - added API key create/list/revoke backend domain in existing service-router-error pattern.
  - stores only keyed hash and prefix, never raw API key in DB.
  - introduced alembic migration for api_keys table and wired router into v1 app routes.