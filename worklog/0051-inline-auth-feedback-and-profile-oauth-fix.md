# fix: preserve oauth links on profile save and inline auth feedback

- scope: cross-cutting
- changed files:
  - backend/app/models/user.py
  - frontend/src/pages/LoginPage.tsx
  - frontend/src/pages/ForgotPasswordPage.tsx
  - frontend/src/pages/SettingsPage.tsx
  - frontend/src/pages/DashboardPage.tsx
  - frontend/src/styles/app.css
- reason and impact:
  - keep oauth provider linkage visible after profile updates by returning refreshed user response.
  - replace card-style auth errors with compact inline messages under relevant inputs.
  - tighten settings content spacing and expose InlineMessage examples in showcase.
