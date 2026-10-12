# 배포 가이드

이 문서는 이 저장소의 구체적인 배포 절차를 정의합니다.

## 1) 사전 요구사항

1. Docker Desktop(또는 Docker Engine)이 설치되어 있고 실행 중이어야 합니다.
2. 현재 작업 디렉터리는 저장소 루트여야 합니다.
3. 로컬 인프라 사용 시 아래 포트가 사용 가능해야 합니다.

- `8000` (app)
- `5432` (postgres)
- `6379` (redis)

Git, Make, Python 3도 필요합니다. 배포 명령은 호스트 uv를 요구하지 않습니다. Compose는 `up --wait --wait-timeout`을 지원해야 합니다.
로컬 프론트엔드 빌드에는 Node.js 24와 npm이 필요하며 Docker 빌드는 이미지 안에서 실행합니다.

## 2) 환경 설정

새 배포 환경 초기화 (기존 파일을 덮어쓰지 않음):

```bash
make docker-init PUBLIC_DOMAIN=app.example.com
```

주 배포 환경 파일:

- `docker/.env`

초기화는 무작위 로컬 인증정보를 생성합니다. 기존 설치는 키를 유지하거나 `docker/.env`의 `SECRET_KEY`를 명시적으로 설정하세요.
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

원샷 배포 (사전 점검 + 이미지 준비 + 서비스 준비 + HTTP 확인):

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
- 오프라인 아카이브가 필요할 때 `docker-export.sh`를 별도로 실행하세요.

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

## 공개 HTTPS 배포와 컨테이너 권한

앱·워커·Beat 이미지는 UID/GID `10001:10001`로 실행하며 Compose에서 Linux
capability와 권한 상승을 차단합니다. 새 데이터 볼륨은 이미지 디렉터리의 쓰기 권한을
물려받습니다. 기존 root 소유 로컬 객체·SQLite·Beat 볼륨은 업그레이드 전에 백업하고
UID/GID 10001로 명시적으로 이전하세요. 대상 볼륨 이름과 사용자 지정
OBJECT_STORAGE_LOCAL_ROOT를 먼저 확인하세요. 기존 데이터 소유권을 자동 변경하지 않습니다.

기본 앱 포트는 `127.0.0.1`에만 공개합니다. 외부 공개 시 DNS를 서버로 연결하고
TCP 80/443을 허용한 뒤 운영 서명 키와 실제 HTTPS APP_BASE_URL·CORS_ORIGINS를
설정하세요. 활성화된 OAuth 콜백과 Stripe 반환·웹훅 주소도 맞추고, API 문서가
필요하지 않으면 SWAGGER_ENABLED=false를 사용하세요. DB 비밀번호도 고유하게 설정하세요.

`docker/.env`에 프록시 구성을 저장해 배포·상태·로그 명령이 동일한 구성을 사용하게 합니다.

```dotenv
COMPOSE_FILE=docker-compose.yml:docker-compose.https.yml
PUBLIC_DOMAIN=app.example.com
APP_BASE_URL=https://app.example.com
CORS_ORIGINS=https://app.example.com
VITE_PUBLIC_SITE_URL=https://app.example.com
```

`make docker-check`, `make docker-deploy`로 배포합니다. **새 설치**는
`make docker-init PUBLIC_DOMAIN=app.example.com`으로 설정과 무작위 로컬 인증정보를
0600 권한 파일에 생성합니다. 기존 파일은 거부합니다.
[단일 서버 AWS/Cloudflare 운영 절차](monolithic-deployment.md)에서 업데이트·이미지 선택·백업과
복구 범위를 확인하세요.

Caddy가 TLS 인증서를 관리하고 공개 metrics·Swagger/Redoc·OpenAPI 접근을 차단합니다.
Prometheus는 내부 `app:8000`으로 접근할 수 있고 SSE는 응답을 버퍼링하지 않고
전달합니다. overlay는 OAuth 리디렉션의 HTTPS 처리를 위해 내부 네트워크에서
전달하는 프록시 헤더를 Uvicorn이 신뢰하도록 설정합니다. 앱 포트를 모든 인터페이스에
열거나 신뢰하지 않는 컨테이너를 같은 네트워크에 연결하지 마세요.

실제 도메인에서 `/health/ready`, 로그인·갱신 쿠키, OAuth 리디렉션과 공개 `/metrics`
차단을 확인하세요. 로컬 TLS 검증은 실제 DNS·인증서 발급·제공자 콜백·백업 복원을
대신하지 않습니다. [Caddy 프록시 문서](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)를 참고하세요.

## 공개 링크 공유 메타데이터

B4React는 정적 HTML에 description·Open Graph·Twitter 태그를 넣습니다.
`docker/.env`의 선택 설정 `VITE_PUBLIC_SITE_URL=https://your-domain.example`와
`VITE_SITE_DESCRIPTION`을 입력한 뒤 `make docker-build`를 실행하고 기존 Compose
오버레이 구성으로 재배포하세요. 공개 프론트엔드 빌드 인자이므로 실행 환경만 바꾸면
HTML은 갱신되지 않습니다. `.env` 파일은 계속 Docker 빌드 컨텍스트에서 제외됩니다.

URL은 자격 증명·경로·쿼리·fragment가 없는 HTTP(S) origin이어야 합니다. 실제 공개
주소가 없으면 비워두세요. 이때 URL·이미지 태그를 생략합니다. 제목은 project.json에서
생성한 프론트엔드 설정을 따릅니다. 사용자 프로젝트는 자체 래스터 로고를 쓰거나
이미지 태그를 생략하며 템플릿 배너를 상속하지 않습니다. 직접 Docker 빌드할 때는
`--build-arg VITE_PUBLIC_SITE_URL=...`, `--build-arg VITE_SITE_DESCRIPTION=...`를 전달합니다.
사전 빌드 이미지는 빌드 당시 값을 유지합니다.
[프론트엔드 공유 규칙](../../src/frontend/notes/ko/sharing.md)을 참고하고 배포 주소의
HTML과 필요한 미리보기 캐시 갱신을 확인하세요.

## 공개 검색 페이지

`VITE_PUBLIC_DISCOVERY=true`와 `VITE_PUBLIC_SITE_URL`로 기본 템플릿의 영문·한국어 소개(/about/, /about/ko/)를 빌드합니다. 이미지 재빌드가 필요하며 재시작만으로는 반영되지 않습니다. 선택 항목 `VITE_INDEXNOW_KEY`는 공개 소유 확인 파일을 생성하고 `INDEXNOW_ENABLED=true`는 배포 정상 응답 검사 후 변경된 공개 URL을 제출합니다. [배포·등록·재시도 안내](search-discovery.md)를 참고하세요.

## 공개 basePath

FastAPI + React 모놀리식 이미지를 Nginx 접두사 아래에서 실행하려면 [basePath 배포](base-path-deployment.md)를 참고하세요.
