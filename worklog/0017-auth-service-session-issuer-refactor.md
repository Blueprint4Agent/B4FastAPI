# refactor: extract shared session issuer in auth service

- scope: backend
- changed files:
  - `backend/app/services/auth.py`
- reason:
  - remove duplicated access/refresh token issuance logic between login and refresh paths.
  - establish a single session issuance entrypoint that can be reused by upcoming OAuth callback flow.
- impact:
  - `login` and `refresh_access_token` now reuse `_issue_session_tokens(...)`.
  - API response and error payload contracts remain unchanged while internal service structure is simplified.
