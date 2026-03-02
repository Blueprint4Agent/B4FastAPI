commit title: feat: add optional SMTP mail integration for signup
scope: backend

changed files:
- backend/app/core/settings.py
- backend/app/main.py
- backend/app/services/auth.py
- backend/app/services/mail.py
- backend/.env.example

reason and impact:
- Added SMTP-related settings and validation paths so email can be configured via environment variables.
- Introduced a mail abstraction with no-op and SMTP providers to keep business logic decoupled from transport.
- Added startup initialization checks so disabled mode is a no-op and enabled mode fails fast on bad SMTP configuration.
- Hooked signup to trigger a best-effort verification email without changing existing auth exception payload behavior.
