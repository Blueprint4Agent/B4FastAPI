# DB 백업 및 복구 런북

이 런북은 PostgreSQL(주 운영)과 SQLite(로컬 대체)의 백업/복구 절차를 다룹니다.

## 1) PostgreSQL 백업

### 1.1 로컬 docker postgres

저장소 루트에서 실행:

```bash
mkdir -p docker/artifacts/db-backups
docker exec -t b4fastapi-postgres pg_dump -U postgres -d template -Fc > docker/artifacts/db-backups/template-$(date +%Y%m%d-%H%M%S).dump
```

### 1.2 외부 postgres

```bash
PGPASSWORD='<db_password>' pg_dump \
  -h <db_host> \
  -p 5432 \
  -U <db_user> \
  -d <db_name> \
  -Fc \
  > <db_name>-$(date +%Y%m%d-%H%M%S).dump
```

## 2) PostgreSQL 복구

### 2.1 로컬 docker postgres로 복구

```bash
cat docker/artifacts/db-backups/<backup_file>.dump | docker exec -i b4fastapi-postgres pg_restore -U postgres -d template --clean --if-exists --no-owner --no-privileges
```

### 2.2 외부 postgres로 복구

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

## 3) SQLite 백업/복구 (로컬 전용)

백업:

```bash
cp src/backend/template.db src/backend/template-$(date +%Y%m%d-%H%M%S).db.bak
```

복구:

```bash
cp src/backend/<backup_file>.db.bak src/backend/template.db
```

## 4) 복구 후 절차

1. 앱이 복구된 DB를 바라보도록 설정
2. head까지 마이그레이션 실행:

```bash
cd src/backend
uv run alembic upgrade head
```

3. 스모크 테스트 실행:

```bash
cd src/backend
uv run pytest tests/test_smoke.py
```

## 5) 운영 참고사항

1. 운영 백업은 암호화된 스토리지에 보관
2. 복구 검증 없는 백업은 불완전하므로 정기적 복구 검증 필수
3. 환경별 백업 보관 정책(retention)을 명시적으로 유지
