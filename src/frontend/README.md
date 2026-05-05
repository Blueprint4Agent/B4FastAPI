# Frontend Quick Guide

This guide is for human contributors working on `src/frontend`.
For full engineering constraints, follow `src/frontend/FRONTEND.md`.
Localized docs rule: place translations under `docs/<locale>/frontend/`.
Current locale example (`ko`): `docs/ko/frontend/README.md`, `docs/ko/frontend/FRONTEND.md`, `docs/ko/frontend/TEST.md`.

## 1) Setup

```bash
cd src/frontend
npm ci
```

## 2) Run Dev Server

```bash
cd src/frontend
npm run dev
```

Default local URL:

- `http://localhost:5173`

API base URL behavior:

- If `VITE_API_BASE_URL` is set, frontend uses that value.
- If not set and current port is `5173` (Vite dev), frontend defaults to `http(s)://<current-host>:8000`.
- Otherwise, frontend defaults to current page origin (same-origin), useful for backend static serving mode.

## 3) API Type Generation

Frontend API contracts are generated from backend OpenAPI:

```bash
cd src/frontend
npm run generate:api
```

Server-optional sync (uses existing generated file when backend is unavailable):

```bash
cd src/frontend
npm run api:sync
```

Generated target:

- `src/api/generated/openapi.ts`

## 4) Format / Check

```bash
cd src/frontend
npm run format
npm run format:check
```

## 5) Test

```bash
cd src/frontend
npm run test
```

Run by layer:

```bash
cd src/frontend
npm run test:unit
npm run test:component
npm run test:integration
```

Run full matrix (unit -> component -> integration -> e2e):

```bash
cd src/frontend
npm run test:all
```

E2E smoke:

```bash
cd src/frontend
npm run test:e2e
```

## 6) Build

```bash
cd src/frontend
npm run build
```

Optional API contract refresh + build:

```bash
cd src/frontend
npm run build:sync
```

Strict API contract refresh from backend + build:

```bash
cd src/frontend
npm run build:strict
```

Notes:

- `npm run build` is server-independent by default (no OpenAPI fetch).
- `npm run build:sync` performs optional OpenAPI refresh before build (fallback to existing generated file on fetch failure).
- `npm run build:strict` requires successful OpenAPI refresh from `localhost:8000` before build.

## 7) Core Frontend Rules (Summary)

- API flow: `generated -> api/<domain> -> hooks/api/<domain> -> pages`
- Domain set rule: `<domain>Api.ts` + `<domain>Error.ts` + `use<Domain>Api.ts` must stay 1:1:1
- Domain hooks are called in page layer, not in feature components
- Feature components receive state/actions via props
- Reusable components belong to `src/components/ui/*` (category folders)
- Domain-specific components belong to `src/components/features/<domain>/*`
- All CSS is managed in `src/styles/app.css`
- New reusable UI components must be showcased in `src/pages/main/ShowCasePage.tsx`

## 8) Before Commit

```bash
cd src/frontend
npm run format
npm run format:check
npm run test
npx tsc --noEmit
npm run build
```
