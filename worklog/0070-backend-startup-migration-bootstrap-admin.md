# 0070 backend startup migration bootstrap admin

- commit title: backend: run startup migrations on active database and enforce bootstrap admin role
- changed file scope:
  - src/backend/app/core/migrations.py
  - src/backend/app/main.py
  - src/backend/app/models/user.py
  - src/backend/README.md
  - src/backend/BACKEND.md
- reason:
  - Startup could appear stalled after Alembic logs because Alembic logging config interfered with runtime visibility.
  - Local schema drift (`users.role` missing) required automatic startup upgrade against the currently configured DB.
  - Bootstrap mode needed deterministic admin role for the bootstrap account.
- impact:
  - Backend now applies Alembic `upgrade head` automatically at startup against the active `DATABASE_URL` without downgrade behavior.
  - Bootstrap user is created/promoted as `admin` in `LOGIN_ENABLED=false` mode.
  - Startup lifecycle logging is clearer and migration orchestration is centralized under `app/core/migrations.py`.
