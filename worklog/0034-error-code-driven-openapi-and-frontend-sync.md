## refactor: unify error code-driven API docs and frontend error handling

- scope: cross-cutting
- changed files:
  - backend/app/core/error/error.py
  - backend/app/core/error/auth_exception.py
  - backend/app/core/error/__init__.py
  - backend/app/routers/v1/auth.py
  - frontend/src/utils/authError.ts
  - frontend/src/api/generated/openapi.ts
- reason and impact:
  - moved reusable error response/documentation builders into `core/error/error.py` so other domains can reuse the same pattern.
  - converted auth router response docs to be derived from `AuthErrorCode` instead of hard-coded status numbers.
  - aligned frontend error parsing with generated OpenAPI schemas and enforced complete error-code mapping with compile-time checks.
  - regenerated OpenAPI TypeScript contract to reflect backend response schema changes.
