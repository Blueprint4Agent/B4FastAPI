# fix: simplify settings profile feedback and compact card behavior

- scope: frontend
- changed files:
  - frontend/src/pages/SettingsPage.tsx
  - frontend/src/styles/app.css
  - frontend/src/locales/en.json
- reason and impact:
  - Removed profile-photo feedback cards from settings photo panel.
  - Tightened compact card style overrides with stronger selector specificity.
  - Removed now-unused photo feedback translation keys.
