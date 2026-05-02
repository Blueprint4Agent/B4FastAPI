# 0077 frontend build decouple and sync modes

- commit title: frontend: decouple default build from backend OpenAPI and add sync modes
- changed file scope:
  - src/frontend/package.json
  - src/frontend/README.md
  - src/frontend/FRONTEND.md
  - src/frontend/src/api/auth/authError.ts
  - src/frontend/src/api/generated/openapi.ts
  - src/frontend/src/locales/en.json
- reason:
  - Default frontend build should not require live backend OpenAPI server.
  - API contract refresh needed clear optional/strict execution paths.
  - Generated OpenAPI schema included `INSUFFICIENT_ROLE`, requiring frontend error-map sync.
- impact:
  - `npm run build` is now server-independent.
  - `build:sync` and `build:strict` provide optional and strict backend contract sync modes.
  - Frontend auth error mapping now handles `INSUFFICIENT_ROLE` without type breakage.
