# feat: add profile image persistence to auth profile API

- scope: backend
- changed files:
  - backend/app/models/user.py
  - backend/app/services/auth.py
  - backend/app/routers/v1/auth.py
  - backend/alembic/versions/0003_users_profile_image_url.py
- reason and impact:
  - Added `users.profile_image_url` persistence and migration.
  - Expanded profile update contract to support `name` and `profile_image_url` patch updates.
  - Exposed profile image through auth user responses so frontend can consume avatar URLs consistently.
