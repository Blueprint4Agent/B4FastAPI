# fix: refine settings profile upload UX and feedback stability

- scope: frontend
- changed files:
  - frontend/src/pages/SettingsPage.tsx
  - frontend/src/components/StatusCard.tsx
  - frontend/src/styles/app.css
- reason and impact:
  - Enabled immediate save on photo selection/remove and kept name save flow separate.
  - Reduced feedback card footprint and introduced compact status variant.
  - Stabilized layout widths/heights so feedback visibility does not shift surrounding UI.
