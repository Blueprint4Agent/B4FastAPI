# feat: expand showcase catalog and add agent usage guide

- scope: cross-cutting
- changed files:
  - `frontend/src/App.tsx`
  - `frontend/src/components/AppNavbar.tsx`
  - `frontend/src/components/ui/DropdownMenu.tsx`
  - `frontend/src/components/ui/index.ts`
  - `frontend/src/pages/DashboardPage.tsx`
  - `frontend/src/pages/LoginPage.tsx`
  - `frontend/src/styles/app.css`
  - `frontend/src/locales/en.json`
  - `README.md`
- reason:
  - showcase needed to become the primary authenticated landing route with clearer component grouping and naming.
  - users needed explicit guidance to request UI composition from Agent using showcased components.
- impact:
  - route and navigation now use `/show-case` as main page.
  - showcase now presents categorized component samples with component name labels and generic dropdown support.
  - README now includes an Agent workflow section for component-driven UI requests.
