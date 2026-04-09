# refactor: align api key delete semantics and auth error mapping

- scope: backend
- changed files:
  - backend/app/core/error/api_key_exception.py
  - backend/app/models/api_key.py
  - backend/app/routers/v1/api_key.py
  - backend/app/services/api_key.py
- reason and impact:
  - rename revoke-oriented API key handlers to delete-oriented names for semantic clarity.
  - keep API key status toggle as non-delete while hard delete remains explicit in delete flow.
  - align dependency/service error handling usage to existing error definitions for consistent API responses.
