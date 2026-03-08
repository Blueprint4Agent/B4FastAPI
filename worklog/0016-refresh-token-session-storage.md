# refactor: switch refresh token storage to session-based keys

- scope: backend
- changed files:
  - `backend/app/utils/token.py`
  - `backend/app/utils/cookies.py`
  - `backend/app/services/auth.py`
  - `backend/app/routers/v1/auth.py`
- reason:
  - replace single `refresh_token:{user_id}` storage with session-scoped storage to support multiple concurrent sessions.
  - move refresh cookie identity from `user_id` cookie to dedicated `session_id` cookie.
- impact:
  - refresh tokens are now validated against `refresh_session:{session_id}` payload containing both user and token.
  - logout still revokes all sessions for the current user by deleting all session keys.
  - refresh endpoint supports deriving `user_id` from `session_id` when body `user_id` is omitted.
