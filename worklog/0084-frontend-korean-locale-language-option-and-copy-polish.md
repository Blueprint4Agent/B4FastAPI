# commit title
frontend: add Korean locale support and polish API key/settings copy

# changed file scope
- src/frontend/src/locales/ko.json
- src/frontend/src/locales/en.json
- src/frontend/src/i18n.ts
- src/frontend/src/pages/settings/SettingsPage.tsx
- src/frontend/src/styles/app.css

# reason
- Add a full Korean translation resource and expose Korean as a selectable language in settings.
- Align profile/API key copy text with requested wording updates in both English and Korean.
- Improve visual alignment of icon/text in the inline API key delete button.

# impact
- Users can switch between English and Korean from Settings > General > Language.
- Profile and API key modal descriptions now use updated wording.
- API key delete button icon/text baseline alignment is corrected.
