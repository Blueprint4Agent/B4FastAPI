# feat: add top navbar with profile dropdown and theme switch

- Scope: `frontend`
- Changed files (key paths):
  - `frontend/src/App.tsx`
  - `frontend/src/components/AppNavbar.tsx`
  - `frontend/src/components/ThemeToggle.tsx`
  - `frontend/src/components/ui/ProfileDropdown.tsx`
  - `frontend/src/components/ui/ThemeToggleButton.tsx`
  - `frontend/src/components/ui/index.ts`
  - `frontend/src/pages/DashboardPage.tsx`
  - `frontend/src/pages/SettingsPage.tsx`
  - `frontend/src/locales/en.json`
  - `frontend/src/styles/app.css`
- Reason:
  - Added a full-width top navigation experience for authenticated pages with compact branding and profile actions.
- Impact:
  - Users can access settings, logout, and theme switching from the navbar dropdown.
  - Theme control now uses a reusable UI toggle component with icon + switch presentation.
