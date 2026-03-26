# feat: wire avatar support across frontend auth/user surfaces

- scope: frontend
- changed files:
  - frontend/src/api/generated/openapi.ts
  - frontend/src/hooks/useAuth.tsx
  - frontend/src/components/AppNavbar.tsx
  - frontend/src/components/ui/ProfileDropdown.tsx
  - frontend/src/components/ui/index.ts
  - frontend/src/components/ui/UserAvatar.tsx
  - frontend/src/components/ui/AvatarUploadField.tsx
  - frontend/src/locales/en.json
- reason and impact:
  - Synced generated OpenAPI types with backend profile image fields.
  - Added reusable avatar rendering/upload UI components.
  - Updated auth context and navbar/profile menu to prefer saved profile images.
  - Localized new avatar upload messages and button labels.
