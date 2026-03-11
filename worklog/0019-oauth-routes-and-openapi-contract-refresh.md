# feat: add oauth routes and refresh frontend openapi contract

- scope: cross-cutting
- changed files:
  - `backend/app/routers/v1/auth.py`
  - `backend/app/services/auth.py`
  - `backend/app/models/oauth.py`
  - `backend/app/core/settings.py`
  - `backend/.env.example`
  - `frontend/src/api/generated/openapi.ts`
  - `frontend/src/api/authApi.ts`
- reason:
  - add OAuth API surface for provider discovery, start redirect, and callback handling.
  - refresh frontend OpenAPI schema/types so client contract reflects new OAuth endpoints and `/config` fields.
- impact:
  - backend now exposes `/api/v1/auth/oauth/providers`, `/api/v1/auth/oauth/{provider}/start`, and `/api/v1/auth/oauth/{provider}/callback`.
  - OAuth callback links/creates auth identities and issues refresh session cookies before redirecting to frontend.
  - frontend generated API types now include OAuth provider schemas and paths.
