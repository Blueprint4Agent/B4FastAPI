# fix: prevent refresh race logout on rapid reload

- scope: backend
- changed files:
  - `backend/app/services/auth.py`
- reason:
  - concurrent refresh requests could race during refresh token rotation and cause unexpected logout on rapid page reload.
- impact:
  - refresh now reuses the current refresh token for the same session and only issues a new access token, improving stability under concurrent refresh calls.
