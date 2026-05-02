# 0071 frontend auth disabled routing and dev api base

- commit title: frontend: disable auth routes when login is off and fix 5173 api base fallback
- changed file scope:
  - src/frontend/src/App.tsx
  - src/frontend/src/components/layout/AppNavbar.tsx
  - src/frontend/src/pages/login/LoginPage.tsx
  - src/frontend/src/pages/settings/SettingsPage.tsx
  - src/frontend/src/utils/apiBase.ts
  - src/frontend/README.md
- reason:
  - In `LOGIN_ENABLED=false` mode, users could still reach auth paths or be redirected through login routes.
  - On Vite dev (`:5173`) without `VITE_API_BASE_URL`, API calls defaulted to same-origin, causing `/config` and user bootstrap fetches to miss backend (`:8000`).
- impact:
  - Auth-related routes are now hard-disabled when login mode is off and redirected to `/show-case`.
  - Logout navigation now avoids sending users to `/login` when login mode is disabled.
  - Dev-mode API base defaults to `http(s)://<host>:8000` on port `5173`, restoring `/config` and user bootstrap loading.
