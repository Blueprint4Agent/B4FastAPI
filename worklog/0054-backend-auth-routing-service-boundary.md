# refactor: [20] align auth routing-service boundaries and typing

- scope: backend
- changed files:
- src/backend/app/services/auth.py
- src/backend/app/routers/v1/auth.py
- src/backend/app/routers/v1/api_key.py
- src/backend/pyproject.toml
- brief reason and impact:
- moved refresh request-context business logic from router to service to preserve transport-only router behavior
- aligned router return typing and auth error response declarations with actual propagated domain errors
- reduced editor/ruff import-format mismatch by enabling Ruff isort combine-as-imports setting
