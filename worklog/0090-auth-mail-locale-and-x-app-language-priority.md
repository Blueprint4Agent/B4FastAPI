# commit title
backend/frontend: localize auth mail templates and prioritize X-App-Language header

# changed file scope
- src/backend/app/core/mail_templates.py
- src/backend/app/core/mail.py
- src/backend/app/core/task_queue/services/mail.py
- src/backend/app/services/auth.py
- src/backend/app/routers/v1/auth.py
- src/backend/tests/api/v1/auth/test_auth_api.py
- src/frontend/src/api/auth/authApi.ts
- src/backend/README.md
- docs/ko/backend/README.md

# reason
- Auth mail language previously depended only on browser-level `Accept-Language`, which can diverge from in-app selected language.
- Mail templates required locale variants for English/Korean and consistent propagation through queue-based delivery.

# impact
- Verification/reset email templates now support `en` and `ko` copy variants.
- Language is carried end-to-end: request header -> auth service -> mail queue payload -> mail sender/template renderer.
- Router now resolves preferred language with priority: `X-App-Language` > `Accept-Language`.
- Frontend auth API calls (`signup`, `resend-verification`, `forgot-password`) send `X-App-Language` based on current i18n locale.
- API tests now validate the language header priority behavior.
