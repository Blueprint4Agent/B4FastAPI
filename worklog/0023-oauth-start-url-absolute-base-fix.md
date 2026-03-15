# fix: use api base for oauth start redirect

- scope: frontend
- changed files:
  - `frontend/src/components/ui/OAuthProviderButton.tsx`
- reason:
  - OAuth provider start path was treated as a relative frontend path, which could prevent redirecting to backend OAuth start endpoint depending on deployment origin.
- impact:
  - OAuth button click now resolves start URL against API base and reliably redirects to backend OAuth flow.
