# commit title
infra: harden docker deploy pipeline and fix alembic revision id overflow

# changed file scope
- root docs/config:
  - README.md
  - DEPLOY.md
  - .dockerignore
  - .gitignore
- docker runtime/deploy:
  - docker/Dockerfile
  - docker/docker-compose.yml
  - docker/.env.example
  - docker/scripts/*
- legacy script cleanup:
  - scripts/bootstrap.sh (removed)
  - scripts/bootstrap.ps1 (removed)
- backend migration chain:
  - src/backend/alembic/versions/0002_auth_identities_multi_provider.py
  - src/backend/alembic/versions/0003_users_profile_image_url.py

# reason
- Standardize deployment under `docker/scripts` and provide one operational deployment guide.
- Support conditional local infra startup (postgres/redis) based on DB/Redis env mode.
- Remove startup race risk by waiting for local infra health before starting app.
- Add image tar export path and ignore artifacts in git.
- Fix alembic migration failure on Postgres where revision id exceeded `alembic_version.version_num` length.

# impact
- Docker deploy flow is explicit and reproducible via `DEPLOY.md`.
- `docker-up.sh` now starts only required services and gates app start on infra health.
- `docker-deploy.sh` performs build + recreate + tar export in one run.
- Alembic startup migration now succeeds on Postgres for existing revision chain.
