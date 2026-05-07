# commit title
backend: normalize ruff formatting across core/settings and auth/api-key services

# changed file scope
- src/backend/app/core/mail_templates.py
- src/backend/app/core/settings.py
- src/backend/app/services/api_key.py
- src/backend/app/services/auth.py

# reason
- Full-repo `ruff format --check` previously reported formatting drift in backend modules.
- Formatting normalization is required to keep style checks deterministic and prevent noise in subsequent feature commits.

# impact
- Applied Ruff-compatible formatting only (no runtime behavior changes).
- Restored clean formatting baseline so full backend format checks pass consistently.
