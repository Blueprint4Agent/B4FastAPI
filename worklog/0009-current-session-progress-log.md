# 0009 Worklog

- Commit title: `chore: migrate frontend API contract to generated OpenAPI types`
- Scope: `cross-cutting`

## Timeline (Cumulative)

- `2026-03-01`:
  - Decision: Keep one cumulative session log in this file and refresh a final summary snapshot.
  - Changed files:
    - `worklog/0009-current-session-progress-log.md`
  - Test results:
    - N/A

- `2026-03-01`:
  - Decision: Enforce build-time OpenAPI type generation instead of runtime schema loading.
  - Decision: Standardize on `generate:api` as the primary command and generate `frontend/src/api/generated/openapi.ts`.
  - Implementation:
    - Added/updated frontend scripts:
      - `generate:api`
      - `generate:api:optional`
      - `api:sync`
      - `build` now runs `generate:api` before `tsc` and `vite build`
    - Switched frontend API layer to consume generated OpenAPI types.
    - Removed hand-written frontend API types file and referenced generated types directly.
  - Changed files:
    - `frontend/package.json`
    - `frontend/package-lock.json`
    - `frontend/scripts/generate-openapi.mjs`
    - `frontend/src/api/http.ts`
    - `frontend/src/api/authApi.ts`
    - `frontend/src/hooks/useAuth.tsx`
    - `frontend/src/hooks/useFeatures.ts`
    - `frontend/src/api/generated/openapi.ts`
    - `frontend/src/api/types.ts` (removed)
  - Test results:
    - `npm run generate:api` passed
    - `npm run generate:api:optional` passed
    - `npm run build` passed

- `2026-03-01`:
  - Decision: Keep the generated OpenAPI output under `src/api/generated/` and treat it as the source of truth for frontend API contracts.
  - Decision: Update docs so future agent work follows the same pattern.
  - Changed files:
    - `README.md`
    - `AGENTS.md`
    - `worklog/0009-current-session-progress-log.md`
  - Test results:
    - Documentation-only updates, no additional runtime test needed

## Summary Snapshot (Update Last)

- Current objective:
  - Stabilize frontend API contract management with build-time generated OpenAPI types.
- Key decisions:
  - Do not use runtime OpenAPI schema loading in frontend code.
  - Use `npm run generate:api` to regenerate API types from `http://localhost:8000/openapi.json`.
  - Keep generated output at `frontend/src/api/generated/openapi.ts`.
  - Frontend API code must import from generated OpenAPI types, not hand-written contract files.
- Files changed in this session:
  - `frontend/package.json`
  - `frontend/package-lock.json`
  - `frontend/scripts/generate-openapi.mjs`
  - `frontend/src/api/http.ts`
  - `frontend/src/api/authApi.ts`
  - `frontend/src/hooks/useAuth.tsx`
  - `frontend/src/hooks/useFeatures.ts`
  - `frontend/src/api/generated/openapi.ts`
  - `frontend/src/api/types.ts` (removed)
  - `README.md`
  - `AGENTS.md`
  - `worklog/0009-current-session-progress-log.md`
  - `worklog/running-log.md` (removed)
- Test status:
  - Frontend build and OpenAPI generation scripts are passing.
- Open items:
  - Keep backend `/openapi.json` available in local/dev/CI where frontend build runs.
