# commit title
backend/frontend: add queue-backed auth mail flow and refactor task queue into core package layout

# changed file scope
- src/backend/app/core/task_queue/__init__.py
- src/backend/app/core/task_queue/worker.py
- src/backend/app/core/task_queue/services/__init__.py
- src/backend/app/core/task_queue/services/mail.py
- src/backend/app/main.py
- src/backend/app/services/auth.py
- src/backend/app/core/mail.py
- src/backend/app/core/settings.py
- src/backend/.env.example
- docker/.env.example
- src/backend/BACKEND.md
- src/backend/README.md
- docs/ko/backend/BACKEND.md
- docs/ko/backend/README.md
- src/frontend/src/pages/login/SignupPage.tsx
- src/frontend/src/pages/login/ForgotPasswordPage.tsx

# reason
- Authentication email delivery needed to move from request-time execution to queued background processing for reliability and extensibility.
- Task queue structure needed to follow the same core/domain-service separation pattern used by error/realtime modules.
- Auth confirmation UX needed to avoid blocking screen transition on email-side latency.

# impact
- Mail send requests are now enqueued and processed by a startup-managed Redis worker with retry and DLQ policy.
- Queue core is standardized under `app/core/task_queue/worker.py`, while mail-specific adapters live under `app/core/task_queue/services/mail.py`.
- Environment supports queue timeout/retry tuning via EMAIL_QUEUE_* variables.
- Signup/Forgot-password pages now transition optimistically to confirmation screens while request execution continues in background.
- Backend English/Korean docs now document the folder-based task queue pattern.
