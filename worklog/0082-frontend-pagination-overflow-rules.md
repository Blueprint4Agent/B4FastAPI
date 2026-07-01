# commit title
frontend: add pagination and overflow rules for API key lists

# changed file scope
- src/frontend/FRONTEND.md
- src/frontend/src/components/features/apiKey/DeveloperApiKeysSection.tsx
- src/frontend/src/components/ui/index.ts
- src/frontend/src/components/ui/navigation/Pagination.tsx
- src/frontend/src/locales/en.json
- src/frontend/src/locales/ko.json
- src/frontend/src/pages/main/ShowCasePage.tsx
- src/frontend/src/styles/app.css
- src/frontend/src/tests/component/pages/settings/SettingsPage.test.tsx

# reason
- Define frontend UI/UX rules for large card collections using standard pagination and scroll-container terminology.
- Prevent API key settings from rendering an unbounded card list when many keys exist.
- Keep localized labels available for accessible pagination controls.

# impact
- API key settings now page card lists after six items.
- Numbered pagination with ellipsis is available as a reusable UI component.
- API key list overflow is constrained inside the settings content area.
- ShowCase now demonstrates card-list pagination with a six-card page size.
- Short final pages reserve empty card slots to keep paginated content dimensions stable.
- Active pagination hover states keep selected-page text contrast in light and dark themes.
