# fix: fail fast on invalid oauth configuration at startup

- scope: backend
- changed files:
  - `backend/app/main.py`
- reason:
  - prevent server from starting with broken OAuth provider configuration.
- impact:
  - application startup now checks OAuth config validation errors first.
  - when OAuth is enabled but required provider config is missing, startup aborts with a clear runtime error.
