# feat: expose connected oauth providers in profile settings

- scope: cross-cutting
- changed files:
  - backend/app/models/user.py
  - frontend/src/api/generated/openapi.ts
  - frontend/src/hooks/useAuth.tsx
  - frontend/src/pages/SettingsPage.tsx
  - frontend/src/styles/app.css
  - frontend/src/locales/en.json
- reason and impact:
  - Added connected OAuth provider list to authenticated user response payload.
  - Surfaced provider connections in settings profile and rendered as icon-included button components.
  - Aligned settings OAuth button appearance/animation/layout with existing button system.
