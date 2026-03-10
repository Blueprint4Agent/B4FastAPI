# feat: add oauth provider settings and domain foundation

- scope: backend
- changed files:
  - `backend/.env.example`
  - `backend/app/core/settings.py`
  - `backend/app/models/oauth.py`
  - `backend/app/services/auth.py`
  - `backend/app/models/user.py`
  - `backend/app/core/error.py`
  - `backend/app/main.py`
- reason:
  - prepare backend for OAuth onboarding with default Google/GitHub provider support in configuration.
  - add provider/domain models and service-level provider config exposure before implementing OAuth start/callback routes.
- impact:
  - backend settings now include OAuth toggles and Google/GitHub endpoints/client credentials.
  - `/config` now exposes `oauth_enabled` and `oauth_providers` alongside existing fields.
  - DAO now has OAuth-oriented user/identity helper methods for upcoming callback flow.
  - auth error codes include OAuth-specific variants for consistent API error envelopes.
