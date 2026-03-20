# feat: add shared spinner component and loading page

- scope: frontend
- changed files:
  - `frontend/src/components/ui/Spinner.tsx`
  - `frontend/src/pages/LoadingPage.tsx`
  - `frontend/src/components/ui/index.ts`
  - `frontend/src/App.tsx`
  - `frontend/src/styles/app.css`
  - `frontend/src/locales/en.json`
- reason:
  - reusable loading UI was needed for consistent session/bootstrap and future async states.
- impact:
  - introduced a generic spinner component with size variants.
  - added a dedicated loading page route and wired protected-layout loading state to use it.
  - added loading-related i18n strings and shared spinner styles.
