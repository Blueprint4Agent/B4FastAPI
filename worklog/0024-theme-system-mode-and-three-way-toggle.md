# feat: add system theme mode and three-way toggle ui

- scope: frontend
- changed files:
  - `frontend/src/hooks/useTheme.ts`
  - `frontend/src/components/ui/ThemeToggleButton.tsx`
  - `frontend/src/components/ThemeToggle.tsx`
  - `frontend/src/components/AppNavbar.tsx`
  - `frontend/src/components/ui/ProfileDropdown.tsx`
  - `frontend/src/styles/app.css`
  - `frontend/src/locales/en.json`
- reason:
  - current theme behavior did not default to browser preference and only supported light/dark toggle.
  - profile menu needed updated placement for theme controls under sign-out.
- impact:
  - theme mode now supports `system`, `light`, `dark` with browser-follow behavior in system mode.
  - theme control UI is icon-based and includes a left-side `Theme` label.
  - dropdown menu now places theme selector below sign-out.
