# feat: add oauth provider buttons to login ui

- scope: frontend
- changed files:
  - `frontend/src/components/ui/OAuthProviderButton.tsx`
  - `frontend/src/components/ui/index.ts`
  - `frontend/src/pages/LoginPage.tsx`
  - `frontend/src/styles/app.css`
  - `frontend/src/locales/en.json`
- reason:
  - expose OAuth entry points on the login page so users can start Google/GitHub sign-in directly.
  - keep login page composition component-first by adding a reusable UI button component.
- impact:
  - login page now fetches enabled OAuth providers and renders provider buttons above email/password form.
  - provider button click navigates to backend OAuth start path for redirect flow.
  - i18n now includes provider button labels and divider text.
