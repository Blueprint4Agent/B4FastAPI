# 배포 가이드

이 문서는 이 저장소의 구체적인 배포 절차를 정의합니다.

## 1) 사전 요구사항

1. Docker Desktop(또는 Docker Engine)이 설치되어 있고 실행 중이어야 합니다.
2. 현재 작업 디렉터리는 저장소 루트여야 합니다.
3. 로컬 인프라 사용 시 아래 포트가 사용 가능해야 합니다.

- `8000` (app)
- `5432` (postgres)
- `6379` (redis)

## 2) 환경 설정

템플릿 환경 파일 초기화:

```bash
bash ./docker/scripts/init-env.sh
```

주 배포 환경 파일:

- `docker/.env`

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
DB_NAME=template.db

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

워크플로:

- `.github/workflows/build.yml`

트리거:

- `main` 대상 Pull request
- 매일 `00:00 KST`에 `main` nightly build (`15:00 UTC`)
- 선택적 `ref` 또는 `pr_number` 입력을 받는 수동 `workflow_dispatch`
- Release published 이벤트
- `v*` 형식의 버전 태그 push
- `main` merge마다 Docker 이미지를 자동 빌드하지는 않습니다.

수동 `ref` 예시:

- `main`
- `v1.0.0`
- `<commit-sha>`

수동 PR build 예시:

- `pr_number=12`는 `refs/pull/12/head`를 build합니다.

파이프라인 job:

- Backend: `uv sync --frozen`, Ruff check, Ruff format check, Pytest
- Frontend: `npm ci`, Prettier check, Vitest, production build
- Docker: release/tag, schedule, 명시적 수동 publish 실행에서만 `docker/Dockerfile` 기반 이미지 빌드

이미지 배포:

- Pull request build는 backend/frontend check만 검증합니다.
- schedule 실행은 `main` 이미지를 `nightly-main`으로 push합니다.
- 기본 수동 실행은 backend/frontend check만 검증합니다.
- 수동 실행은 `publish_image=true`를 설정한 경우에만 선택한 ref 이미지를 push합니다.
- 수동 이미지 publish에서 `ref`와 `pr_number`가 모두 비어 있으면 `main` ref와 `main` 이미지 태그를 기본으로 사용합니다.
- 수동 이미지 publish에서 `ref=main`을 지정해도 `main` 이미지 태그를 사용합니다.
- Release published 이벤트와 `v*` 태그 push는 GitHub Container Registry로 push합니다.

기본 이미지 registry:

- `ghcr.io/<owner>/<repo>`

## 6) 데스크톱 빌드 파이프라인

워크플로:

- `.github/workflows/desktop-build.yml`

트리거:

- 수동 `workflow_dispatch`
- 매일 `01:00 KST`에 `main` scheduled build (`16:00 UTC`)
- Release published 이벤트
- `v*` 형식의 버전 태그 push

파이프라인 job:

- macOS Apple Silicon: `macos-14`, target `aarch64-apple-darwin`
- macOS Intel: `macos-13`, target `x86_64-apple-darwin`
- Linux x64: `ubuntu-22.04`
- Windows x64: `windows-latest`

데스크톱 서버 origin:

- 수동 실행은 `api_base_url`을 입력받습니다.
- `api_base_url`을 생략하면 repository/environment variable `DESKTOP_API_BASE_URL`을 사용합니다.
- 둘 다 없으면 데스크톱 빌드는 `http://localhost:8000`으로 fallback합니다.
- 선택된 값은 Tauri 빌드 전에 `VITE_API_BASE_URL`로 프론트엔드에 전달됩니다.

데스크톱 artifact:

- 워크플로는 생성된 installer/bundle을 GitHub Actions artifact로 업로드합니다.
- scheduled `main` 빌드는 내부 검증용 workflow artifact로 보관됩니다.
- Release published 이벤트와 `v*` 태그 push는 생성된 데스크톱 bundle을 해당 GitHub Release asset에도 업로드합니다.
- 현재 unsigned artifact는 내부 빌드 검증용으로 사용할 수 있습니다.
- 공개 배포에는 이후 macOS/Windows signing 및 notarization 단계가 필요합니다.

## 7) 배포 후 검증

실행 중 컨테이너 확인:

```bash
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
```

앱 헬스 엔드포인트 확인:

```bash
curl -i http://localhost:8000/docs
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
