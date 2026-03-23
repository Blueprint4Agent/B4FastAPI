chore: add profile update api and dedicated error code

- scope: backend
- changed files:
  - backend/app/core/error/auth_exception.py
  - backend/app/models/user.py
  - backend/app/routers/v1/auth.py
  - backend/app/services/auth.py
- reason and impact:
  - add `PATCH /api/v1/auth/me` to update user name from settings page.
  - introduce `PROFILE_UPDATE_FAILED` to avoid reusing unrelated `USER_NOT_FOUND` for profile update failures.
  - keep auth router/service error responses aligned with code-driven OpenAPI error contracts.
