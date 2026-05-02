# 0072 frontend settings role badge and scenario sync

- commit title: frontend: finalize settings role badge flow and scenario fixture sync
- changed file scope:
  - src/frontend/TEST.md
  - src/frontend/src/App.tsx
  - src/frontend/src/hooks/useAuth.tsx
  - src/frontend/src/locales/en.json
  - src/frontend/src/styles/app.css
  - src/frontend/src/tests/component/pages/settings/SettingsPage.test.tsx
  - src/frontend/src/tests/fixtures/fullSystemScenarioData.ts
- reason:
  - Remaining frontend edits from settings/admin badge and login-disabled bootstrap flow needed to be captured together.
  - Test and fixture layers required synchronization so role-aware behavior stays verifiable.
- impact:
  - Settings role-badge behavior and related UX/text styles are aligned with current auth model.
  - Component test scenarios and fixture contracts now cover role-specific rendering consistently.
  - TEST guide is updated to reflect the active frontend test organization.
