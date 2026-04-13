# chore: default redis in-memory mode enabled

- commit title: chore: default redis in-memory mode enabled
- scope: backend
- changed files:
  - backend/app/core/settings.py
- reason and impact:
  - Change the default of `REDIS_IN_MEMORY` from `false` to `true`.
  - Local backend runs use fakeredis by default unless env overrides it.
