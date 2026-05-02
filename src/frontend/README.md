# Frontend Quick Guide

This guide is for human contributors working on `src/frontend`.
For full engineering constraints, follow `src/frontend/FRONTEND.md`.

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

Notes:

- `npm run build` includes `generate:api`, TypeScript compile, Vite build, and copy-to-backend static sync.

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
