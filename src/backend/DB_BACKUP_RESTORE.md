# DB Backup and Restore Runbook

This runbook covers backup and restore for PostgreSQL (primary) and SQLite (local fallback).

## 1) PostgreSQL Backup

### 1.1 Local docker postgres

Run from repository root:

```bash
mkdir -p docker/artifacts/db-backups
docker exec -t b4fastapi-postgres pg_dump -U postgres -d template -Fc > docker/artifacts/db-backups/template-$(date +%Y%m%d-%H%M%S).dump
```

### 1.2 External postgres

```bash
PGPASSWORD='<db_password>' pg_dump \
  -h <db_host> \
  -p 5432 \
  -U <db_user> \
  -d <db_name> \
  -Fc \
  > <db_name>-$(date +%Y%m%d-%H%M%S).dump
```

## 2) PostgreSQL Restore

### 2.1 Restore into local docker postgres

```bash
cat docker/artifacts/db-backups/<backup_file>.dump | docker exec -i b4fastapi-postgres pg_restore -U postgres -d template --clean --if-exists --no-owner --no-privileges
```

### 2.2 Restore into external postgres

```bash
PGPASSWORD='<db_password>' pg_restore \
  -h <db_host> \
  -p 5432 \
  -U <db_user> \
  -d <db_name> \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  <backup_file>.dump
```

## 3) SQLite Backup/Restore (Local Only)

Backup:

```bash
cp src/backend/template.db src/backend/template-$(date +%Y%m%d-%H%M%S).db.bak
```

Restore:

```bash
cp src/backend/<backup_file>.db.bak src/backend/template.db
```

## 4) Post-Restore Steps

1. Point app to restored DB target.
2. Run migration to head:

```bash
cd src/backend
uv run alembic upgrade head
```

3. Run smoke tests:

```bash
cd src/backend
uv run pytest tests/test_smoke.py
```

## 5) Operational Notes

1. Keep production backups in encrypted storage.
2. Validate restore path regularly; backup without restore test is incomplete.
3. Keep backup retention policy explicit per environment.
