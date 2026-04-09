# feat: align auth dependencies and swagger token flow

- scope: backend
- changed files:
  - backend/app/deps.py
  - backend/app/routers/v1/auth.py
  - backend/app/core/error/api_key_exception.py
  - backend/pyproject.toml
  - backend/uv.lock
- reason and impact:
  - enabled swagger oauth2 password token flow for email/password auth.
  - kept bearer token and api key as OR auth options in dependency-based validation.
  - converted deps-layer auth failures to domain error-code based responses.