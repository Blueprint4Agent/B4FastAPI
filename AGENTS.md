# Agent Customization Guide

This document maps the fastest edit points for an agent.

## 1) Change auth rules

- File: `backend/app/services/auth.py`
- Why: password/login/session policies are centralized here.
- Common edits:
  - Add MFA checks after `verify_password(...)`
  - Add account status checks before token issuance
  - Change lockout policy in `_check_login_limit` / `_increase_login_fail_count`

## 2) Change token/cookie strategy

- File: `backend/app/utils/token.py`
  - Update claims, expiry, signing algorithm
- File: `backend/app/utils/cookies.py`
  - Update cookie names, secure/samesite policy, remember-me max-age

## 3) Add new API routes

- File: `backend/app/routers/v1/auth.py`
  - Keep this file transport-focused (request/response)
  - Call service methods for business logic
- File: `backend/app/main.py`
  - Register router prefix and tags

## 4) Change DB/Redis providers

- File: `backend/app/core/settings.py`
  - Add env variables
  - Keep backward-compatible env names when possible
- File: `backend/app/core/database.py`
  - Replace `create_all` with Alembic when schema versioning is needed
- File: `backend/app/core/redis.py`
  - Replace single Redis with cluster/sentinel client

## 5) Frontend auth flow changes

- File: `frontend/src/hooks/useAuth.tsx`
  - Session bootstrap and login/logout lifecycle
- File: `frontend/src/api/authApi.ts`
  - Endpoint contract changes
- File: `frontend/src/pages/*.tsx`
  - UI behavior and form validation UX

## 6) Frontend API contract management (required)

- Source of truth for frontend API schemas:
  - `http://localhost:8000/openapi.json`
- Generated output file:
  - `frontend/src/api/generated/openapi.ts`
- Required scripts:
  - `npm run generate:api`
  - `npm run build` (must run `generate:api` first)
- Rules:
  - Import API schema/types from `frontend/src/api/generated/openapi.ts`.
  - Do not maintain duplicate hand-written API contract types for OpenAPI-backed endpoints.
  - If endpoint contracts change, regenerate types before editing API call sites.

## 7) Frontend design changes (component-first, required)

- Always inspect and change UI in component units first.
- Priority order:
  - `frontend/src/components/ui/*` (Button, InputField, PanelCard, ValidationCard, etc.)
  - `frontend/src/components/*` (feature-level wrappers)
  - `frontend/src/pages/*.tsx` (composition only, minimal markup)
- Do not directly add raw `<button>`, `<input>`, or card markup in pages when an existing
  component can be reused.
- If a design change is needed and no matching component exists, add a reusable component under
  `frontend/src/components/ui/` and then consume it from pages.
- Keep style updates tied to component class names in `frontend/src/styles/app.css`.
- Before finishing, confirm pages still compose from components and run `npm run build`.

## 8) Minimum contracts to keep stable

- API payload shape for auth errors:
```json
{
  "detail": {
    "error": "CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```
- `/config` response should include:
  - `api_base_path`
  - `login_enabled`
  - `frontend_base_path`

## 9) Commit message convention (required)

- Split commits by domain and feature:
  - Frontend commits: UI/components/pages/style/i18n changes
  - Backend commits: API/service/model/db/infra changes
- Keep each commit focused on one feature unit.
- Commit message format:
  - Title: `type: short-summary`
  - Body: 1 to 4 bullet lines (`- ...`) describing concrete features/changes
- Preferred `type`:
  - `feat`, `fix`, `refactor`, `chore`, `docs`, `test`
- Example:
```text
chore: fix auth form validation flow

- move validation messages to warning cards
- enforce password pattern in signup/login
- align frontend and backend constraints
```

## 10) Worklog convention (required)

- Do not use root `WORKLOG.md`.
- Keep all logs in `worklog/`.
- For each commit, create one markdown log file:
  - filename pattern: `worklog/XXXX-<short-slug>.md`
  - `XXXX` starts at `0001` and increments by 1
- Each worklog file should include:
  - commit title
  - scope (`frontend` or `backend` or `cross-cutting`)
  - changed files (key paths)
  - brief reason and impact

## 11) Error response pattern for API expansion (required)

- When adding a new domain/service error module, follow the same pattern used by auth:
  - Define domain error codes as `Enum` values of `ServiceErrorCode`.
  - Generate domain error schema models via `build_error_models(...)` in `backend/app/core/error/error.py`.
  - Build OpenAPI error responses from error codes via `build_error_responses_from_codes(...)` (no hard-coded status numbers in routers).
- Router usage rule:
  - In route decorators, pass domain error enums to a domain helper (e.g. `xxx_error_responses(ErrorCode.A, ErrorCode.B)`), not raw `400/401/500` literals.
- Frontend usage rule:
  - Parse and map backend error codes based on generated `frontend/src/api/generated/openapi.ts` schemas.
  - Keep error-code translation maps exhaustive (`Record<ErrorCode, ...>`) to fail fast on newly added backend codes.
