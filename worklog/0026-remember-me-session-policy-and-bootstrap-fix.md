# fix: align remember-me persistence and session bootstrap recovery

- scope: cross-cutting
- changed files:
  - `backend/app/utils/token.py`
  - `backend/app/services/auth.py`
  - `backend/app/routers/v1/auth.py`
  - `backend/app/utils/cookies.py`
  - `frontend/src/hooks/useAuth.tsx`
  - `frontend/src/locales/en.json`
- reason:
  - remember-me preference was not consistently preserved during refresh, causing unexpected persistence behavior.
  - dashboard bootstrap could redirect to login on transient `me` failure without attempting refresh recovery.
- impact:
  - refresh session now keeps `remember_me` metadata and re-applies cookie policy consistently on refresh.
  - secure cookie detection now respects forwarded HTTPS headers in proxy environments.
  - auth bootstrap now retries via refresh on `me` failure and de-duplicates concurrent refresh calls.
  - login UI label now uses simplified `Remember me` wording.
