feat: add reusable menu list component and settings profile save ui

- scope: frontend
- changed files:
  - frontend/src/components/ui/MenuList.tsx
  - frontend/src/components/ui/PrimaryCard.tsx
  - frontend/src/components/ui/index.ts
  - frontend/src/pages/SettingsPage.tsx
  - frontend/src/pages/DashboardPage.tsx
  - frontend/src/styles/app.css
  - frontend/src/api/authApi.ts
  - frontend/src/hooks/useAuth.tsx
  - frontend/src/utils/authError.ts
  - frontend/src/locales/en.json
  - frontend/src/api/generated/openapi.ts
- reason and impact:
  - build settings profile save flow with loading button and success/error status cards.
  - extract menu list into reusable `MenuList` component and expose it in showcase.
  - align frontend API contract and auth error mapping with backend profile update endpoint/code.
