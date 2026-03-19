# feat: refine login remember options behavior and layout

- scope: frontend
- changed files:
  - `frontend/src/pages/LoginPage.tsx`
  - `frontend/src/locales/en.json`
  - `frontend/src/styles/app.css`
- reason:
  - remember options were auto-enabled unexpectedly and checkbox ordering/spacing needed better UX.
- impact:
  - `Remember email` and `Remember me` now persist only when users explicitly choose them.
  - login form shows `Remember email` above `Remember me` with tighter spacing.
  - login text updated to use simplified remember labels.
