# 0063 Worklog

- Commit title: `fix: align oauth callback redirect contract and openapi sync`
- Scope: `backend-auth-router`, `frontend-openapi-generated`, `backend-guide`

## Changed Files

- `src/backend/app/routers/v1/auth.py`
- `src/frontend/src/api/generated/openapi.ts`
- `src/backend/BACKEND.md`

## Reason

- OAuth callback endpoint documented JSON domain error responses while runtime behavior returned redirects on failure paths.
- This mismatch caused OpenAPI contract drift and confusion during frontend type sync.

## Impact

- OAuth callback route contract is now redirect-oriented and aligned with runtime behavior.
- Frontend generated OpenAPI types now reflect callback `307` flow rather than JSON error payloads for that endpoint.
- Backend guide now includes explicit rule to keep redirect endpoint docs aligned with transport behavior.
