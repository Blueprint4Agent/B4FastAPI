# refactor: streamline backend logging flow and levels

- scope: cross-cutting
- changed files:
  - src/backend/app/core/logging.py
  - src/backend/app/main.py
  - src/backend/app/core/settings.py
  - src/backend/app/core/mail.py
  - src/backend/app/services/auth.py
  - src/backend/app/services/api_key.py
  - src/backend/app/routers/v1/auth.py
  - src/backend/app/routers/v1/api_key.py
  - src/backend/.env.example
  - README.md
- reason: unify log-level based control, reduce duplicate logs between router/service, and standardize exception logging points.
- impact: cleaner operational logs with lower duplication, clearer error visibility, and stable formatting baseline across backend/frontend checks.
