# commit title
frontend: add main-only toggle sidebar fixed to left edge

# changed file scope
- src/frontend/src/App.tsx
- src/frontend/src/components/layout/AppSidebar.tsx
- src/frontend/src/styles/app.css
- src/frontend/src/locales/en.json
- src/frontend/src/components/features/apiKey/DeveloperApiKeysSection.tsx
- src/frontend/src/utils/date.ts

# reason
- Introduce a left-edge sidebar that can collapse/expand and only appears on the main showcase page.
- Align sidebar behavior with requested UX: hidden on non-main pages and square hover target in collapsed state.
- Keep i18n coverage for new sidebar controls.

# impact
- `/show-case` now renders with a fixed left sidebar and toggle button.
- Non-main pages (for example `/settings`) no longer render the global sidebar.
- Collapsed sidebar interaction area is reduced and square-shaped.
- Frontend build remains successful after layout and style changes.
