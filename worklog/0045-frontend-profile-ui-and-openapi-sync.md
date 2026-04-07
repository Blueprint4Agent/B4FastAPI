# chore: sync frontend profile surfaces and generated api contract

- scope: frontend
- changed files:
  - frontend/src/api/generated/openapi.ts
  - frontend/src/components/StatusCard.tsx
  - frontend/src/components/ui/ProfileDropdown.tsx
  - frontend/src/pages/DashboardPage.tsx
  - frontend/src/pages/SettingsPage.tsx
- reason and impact:
  - synchronized generated OpenAPI typings with current backend contract.
  - updated profile-related UI composition and display behavior in dashboard/settings surfaces.
  - kept frontend changes grouped to preserve clear API/UI commit boundaries.