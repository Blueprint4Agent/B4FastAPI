# 0003 Worklog

- Commit title: `chore: add docker stack and bootstrap scripts`
- Scope: `project-setup`

## Changed Files

- `docker/.env.example`
- `docker/docker-compose.yml`
- `scripts/bootstrap.ps1`
- `scripts/bootstrap.sh`
- `worklog/0003-docker-and-bootstrap-setup.md`

## Reason

- Provide optional local infrastructure (Postgres/Redis) via Docker Compose.
- Standardize one-command environment bootstrap for Windows and Unix shells.

## Impact

- New contributors can initialize `.env` files quickly.
- Infrastructure startup steps become reproducible across environments.
