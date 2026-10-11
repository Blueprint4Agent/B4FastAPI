# 배포 가이드

이 문서는 이 저장소의 구체적인 배포 절차를 정의합니다.

## 1) 사전 요구사항

1. Docker Desktop(또는 Docker Engine)이 설치되어 있고 실행 중이어야 합니다.
2. 현재 작업 디렉터리는 저장소 루트여야 합니다.
3. 로컬 인프라 사용 시 아래 포트가 사용 가능해야 합니다.

- `8000` (app)
- `5432` (postgres)
- `6379` (redis)

Git, Make, Python/uv도 필요합니다. Compose는 `up --wait --wait-timeout`을 지원해야 합니다.
로컬 프론트엔드 빌드에는 Node.js 24와 npm이 필요하며 Docker 빌드는 이미지 안에서 실행합니다.

## 2) 환경 설정

템플릿 환경 파일 초기화:

```bash
make init
```

주 배포 환경 파일:

- `docker/.env`

배포 전에 `docker/.env`의 `SECRET_KEY`를 고유한 난수로 설정하세요.
`python3 -c "import secrets; print(secrets.token_urlsafe(48))"`로 생성할 수 있습니다.
DB/Redis 비밀번호, 공개 APP_BASE_URL·CORS_ORIGINS와 활성화할 연동 설정도 확인하세요.
기존 키는 자동 교체하지 마세요. [운영 키 정책](runtime-modes-rbac.md)을 참고하세요.

## 3) 배포 모드

`docker/scripts/docker-up.sh`는 로컬 `postgres`/`redis` 컨테이너를 시작할지 여부를 결정합니다.
로컬 인프라를 선택하면 이제 `app` 시작 전에 컨테이너 헬스 상태를 기다립니다.

### 모드 A: App + 로컬 Postgres + 로컬 Redis

`docker/.env`에 다음 값을 사용합니다.

```dotenv
DB_DRIVER=postgresql+asyncpg
DB_HOST=postgres
DB_PORT=5432
DB_NAME=template
DB_USER=postgres
DB_PASSWORD=postgres

REDIS_IN_MEMORY=false
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
```

결과:

- 시작: `app`, `postgres`, `redis`

### 모드 B: App + 외부 Postgres + 외부 Redis

`docker/.env`에 다음 값을 사용합니다.

```dotenv
DB_DRIVER=postgresql+asyncpg
DB_HOST=<external-db-host>
DB_PORT=5432
DB_NAME=<db-name>
DB_USER=<db-user>
DB_PASSWORD=<db-password>

REDIS_IN_MEMORY=false
REDIS_HOST=<external-redis-host>
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<optional>
```

결과:

- 시작: `app`만

### 모드 C: App + SQLite + In-Memory Redis

`docker/.env`에 다음 값을 사용합니다.

```dotenv
DB_DRIVER=sqlite+aiosqlite
DB_NAME=/var/lib/b4fastapi/database/template.db

REDIS_IN_MEMORY=true
```

결과:

- 시작: `app`만

## 4) 표준 명령어

앱 이미지 빌드:

```bash
bash ./docker/scripts/docker-build.sh
```

서비스 시작:

```bash
bash ./docker/scripts/docker-up.sh
```

서비스 중지:

```bash
bash ./docker/scripts/docker-down.sh
```

로그 보기:

```bash
bash ./docker/scripts/docker-logs.sh app
```

원샷 배포 (빌드 + 재기동 + tar 내보내기):

```bash
bash ./docker/scripts/docker-deploy.sh
```

이미지 tar만 내보내기:

```bash
bash ./docker/scripts/docker-export.sh
```

내보내기 경로:

- `docker/artifacts/`

## 5) GitHub Actions 빌드 파이프라인

`.github/workflows/build.yml`은 수동 `workflow_dispatch`로만 실행합니다.
PR·push·태그·release·schedule 이벤트는 자동 실행하지 않습니다. 로컬 훅이 검증을
수행하며, PR 보호 규칙과 서버 측 테스트 강제는 별개입니다.

- `ref`: 브랜치·태그·커밋 SHA. `pr_number`가 있으면 `refs/pull/<번호>/head`를 우선합니다.
- `publish_image=false`(기본): 백엔드/프론트엔드 검증만 수행합니다.
- `publish_image=true`: 검증 후 선택한 이미지를 `ghcr.io/<owner>/<repo>`에 빌드·push합니다.
  ref와 PR 번호가 모두 없으면 `main`을 선택합니다.
- 이미지 태그는 `manual-<정규화된-ref>`(예: `manual-main`), PR 선택 시
  `manual-pr-<번호>`, 짧은 SHA 태그입니다. `nightly-main`이나 버전 이미지를 자동 발행하지 않습니다.

백엔드와 프론트엔드 job은 전체 검증을 사용하며 프론트엔드 서브모듈은 고정된 버전을
재귀 체크아웃합니다. 이미지 공개는 명시적인 작업이므로 실행 전에 대상 버전을 확인하세요.

## 6) 데스크톱 빌드 파이프라인

`.github/workflows/desktop-build.yml`도 수동 `workflow_dispatch`로만 실행합니다.
자동 schedule·release·tag 트리거는 없습니다.

| 플랫폼 | Runner | Rust target |
| --- | --- | --- |
| macOS Apple Silicon | macos-14 | aarch64-apple-darwin |
| macOS Intel | macos-15-intel | x86_64-apple-darwin |
| Linux x64 | ubuntu-22.04 | runner 기본값 |
| Windows x64 | windows-latest | runner 기본값 |

`api_base_url`, `DESKTOP_API_BASE_URL`, `http://localhost:8000` 순으로 서버 주소를
선택합니다. 배포용 빌드에는 실제 API 주소를 설정하세요. `VITE_API_BASE_URL`로
프론트엔드에 포함되며 백엔드는 데스크톱 번들에 포함되지 않습니다.

설치 파일/번들은 Actions artifact로 14일간 보관합니다. 수동으로 태그 ref를 선택하면
Tauri action에 release 메타데이터를 전달하며, 일반 브랜치 실행은 태그 release를 만들지
않습니다. 현재 산출물은 서명되지 않았으므로 공개 배포에는 서명·공증과 설치 검증이 필요합니다.

## 7) 배포 후 검증

실행 중 컨테이너 확인:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

앱 헬스 엔드포인트 확인:

```bash
curl --fail http://localhost:8000/health/live
curl --fail http://localhost:8000/health/ready
curl -i http://localhost:8000/config
```

시작 시 마이그레이션 로그 확인:

- `Database schema migration check complete (target=head).`

## 8) 트러블슈팅

`docker command not found`

- Docker Desktop/Engine을 설치하고 Docker 데몬이 실행 중인지 확인하세요.

앱은 시작되지만 DB 연결 실패

- `docker/.env`의 `DB_DRIVER/DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD`를 확인하세요.
- 로컬 postgres 사용 시 `DB_HOST`는 반드시 `postgres`여야 합니다.

Redis 연결 실패

- 로컬 redis 컨테이너 사용: `REDIS_IN_MEMORY=false` 및 `REDIS_HOST=redis`
- 외부 redis 사용: `REDIS_HOST`를 외부 호스트로 설정하고 `REDIS_IN_MEMORY=false` 유지

Alembic 시작 마이그레이션이 revision 길이 오류로 실패

- Alembic `revision` ID는 `alembic_version.version_num` 제약 길이를 넘지 않도록 유지하세요.

tar 아티팩트가 생성되지 않음

- `docker-build.sh`는 tar를 내보내지 않습니다.
- `docker-deploy.sh` 또는 `docker-export.sh`를 사용하세요.

## 프론트 소스와 패키징

로컬 Docker 빌드 전에 `make frontend-init`으로 고정된 B4React를 초기화합니다.
Build·Desktop CI는 recursive checkout을 사용합니다. 프론트는 자체 dist만 생성하고
부모 Dockerfile이 FastAPI 정적 경로에 복사합니다. 로컬 통합 실행은
`make frontend-package` 또는 `make build`를 사용합니다.
서브모듈 갱신 시 제공자 스냅샷·소비자 계약·생성 타입 검사를 모두 통과해야 합니다.
기존 데스크톱 bundle 식별자는 이번 분리에서 유지합니다.

## SQLite 영속성과 기존 배포

SQLite는 API와 워커에 `/var/lib/b4fastapi/database`로 연결한 `sqlite_data`
이름 있는 볼륨을 사용합니다. `docker-up`은 상대 경로·`..`를 포함하여 해당 디렉터리
밖의 경로를 서비스 시작/재생성 전에 거부합니다. 메모리 Redis는 영속적이지 않으며
API 프로세스 간 공유되지 않으므로 다중 프로세스에서는 실제 Redis를 사용하세요.
기본 배포 데이터베이스는 PostgreSQL입니다.

기존 SQLite 컨테이너에서는 쓰기와 워커를 멈추고 SQLite 백업 기능으로 백업한 뒤,
기존 컨테이너를 재생성/삭제하기 **전에** 백업을 외부로 복사하세요. 새 볼륨에 백업을
가져오고 위의 절대 DB_NAME 경로를 설정한 후, 계정과 Alembic 버전을 확인하고
트래픽을 재개하세요. DB_NAME만 변경하면 다른 데이터베이스를 생성하며 기존 파일은
자동 이전되지 않습니다. Compose 프로젝트 이름을 유지하고, 데이터를 보존할 때
`docker compose down -v`를 실행하지 마세요. [백업/복원](backend/DB_BACKUP_RESTORE.md)을 참고하세요.
