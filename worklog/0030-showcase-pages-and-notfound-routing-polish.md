# feat: polish showcase pages and not-found routing behavior

- scope: frontend
- changed files:
  - `frontend/src/App.tsx`
  - `frontend/src/components/AppNavbar.tsx`
  - `frontend/src/hooks/useTheme.ts`
  - `frontend/src/locales/en.json`
  - `frontend/src/pages/DashboardPage.tsx`
  - `frontend/src/pages/ShowCaseNotFoundPage.tsx`
  - `frontend/src/styles/app.css`
- reason:
  - showcase needed page-level previews and better not-found UX with consistent navigation/title behavior.
  - loading/404 states required clearer route handling and visual alignment with theme/nav.
- impact:
  - added showcase sub-routes for loading and 404 previews.
  - non-existent routes now render a real 404 page instead of redirecting to showcase.
  - navbar page title now reflects loading and not-found states.
  - not-found page messaging/actions and center alignment were refined.
