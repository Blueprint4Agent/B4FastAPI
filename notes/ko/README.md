# Blueprint4FastAPI

Blueprint4FastAPI는 다음 구성을 갖춘 풀스택 템플릿입니다.

- 백엔드: FastAPI + SQLAlchemy + Alembic + Redis
- 프론트엔드: React + TypeScript + OpenAPI 기반 API 타입 생성
- 선택형 데스크톱 셸: 동일한 React 프론트엔드를 사용하는 Tauri 2
- 모놀리식 정적 서빙 지원 (프론트 빌드를 백엔드 static 경로로 복사)

## 문서 시작점

1. 에이전트/워크플로 규칙: `AGENTS.md`
2. 배포 가이드: `DEPLOY.md`
3. 백엔드 엔지니어링 규칙: `src/backend/BACKEND.md`
4. 프론트엔드 엔지니어링 규칙: `src/frontend/FRONTEND.md`
5. 백엔드 빠른 가이드: `src/backend/README.md`
6. 프론트엔드 빠른 가이드: `src/frontend/README.md`
7. 공통 API 계약: `contracts/README.md` (`contracts/openapi.json`)

한국어 문서:

1. 루트 가이드: `notes/ko/README.md`
2. 에이전트/워크플로 규칙: `notes/ko/AGENTS.md`
3. 배포 가이드: `notes/ko/DEPLOY.md`
4. 백엔드 엔지니어링 규칙: `notes/ko/backend/BACKEND.md`
5. 프론트엔드 엔지니어링 규칙: `notes/ko/frontend/FRONTEND.md`
6. 백엔드 빠른 가이드: `notes/ko/backend/README.md`
7. 프론트엔드 빠른 가이드: `notes/ko/frontend/README.md`
8. API 계약: `notes/ko/contracts/README.md`

## 저장소 구조

```text
contracts/
src/
  backend/
  frontend/  # B4React Git submodule
docker/
  scripts/
```

## 빠른 시작

1. 환경 파일 초기화:

```bash
make init
```

2. 백엔드 실행 (로컬 개발):

```bash
make backend-install
make backend-dev
```

3. 프론트엔드 실행 (로컬 개발):

```bash
make frontend-install
make frontend-dev
```

4. 접속:

- 백엔드 API 문서: `http://localhost:8000/docs`
- 프론트엔드 앱 (Vite): `http://localhost:5173`

## Make 워크플로 훅

사용 가능한 워크플로 훅은 `make help`로 확인합니다.

자주 쓰는 타겟:

```bash
make install              # 백엔드/프론트엔드 의존성 설치
make backend-dev          # FastAPI 개발 서버 실행
make frontend-dev         # Vite 개발 서버 실행
make build                # 백엔드 환경 및 프론트엔드 아티팩트 빌드
make test                 # 백엔드/프론트엔드 테스트 실행
make check                # 백엔드 린트 및 프론트엔드 포맷 체크
make format               # 백엔드/프론트엔드 포맷팅
make ci                   # check, test, build 실행
```

Docker 타겟:

```bash
make docker-build
make docker-up
make docker-logs DOCKER_SERVICE=app
make docker-down
make docker-deploy
make docker-export
make docker-observability-up
make docker-observability-down
```

`make docker-observability-down`은 Grafana, Prometheus, OpenTelemetry Collector,
Tempo만 중지합니다. 앱, PostgreSQL, Redis는 계속 실행됩니다. 중지된 컨테이너와
데이터 볼륨은 유지되며, `make docker-observability-up`으로 관측성 서비스를
다시 시작할 수 있습니다.

## 환경파일 관리

```bash
make env-sync          # 개발 환경 갱신 (백엔드/프론트엔드)
make env-check         # 개발 환경 키·배치 검사
make docker-env-sync   # 배포 환경 갱신 (docker/.env)
make docker-env-check  # 배포 환경 키·배치 검사
make env-contract-check # 백엔드·Docker 예제의 공통 키만 검사
```

`uv`가 필요하며 개발용 명령은 초기화된 B4React 서브모듈도 필요합니다.
각 명령은 대상 디렉터리의 `.env`를 해당 `.env.example`과 비교합니다.
sync는 예제의 주석·빈 줄·키 순서에 맞춰 파일을 재구성하며, 기존 값은 빈 값과
따옴표·이스케이프를 포함해 그대로 보존합니다. 새 키에는 예제 기본값을 사용합니다.
직접 작성한 주석은 예제 주석으로 교체되며 원본은 백업에서 확인할 수 있습니다.
예제에 없는 키는 알림 후 파일 끝의 별도 구역에 보존합니다. 누락·중복 키,
잘못된 문법, 주석·배치 불일치는 검사 실패로 처리합니다. 백엔드와 Docker 예제의
키는 Docker 전용 `APP_IMAGE`, `GRAFANA_ADMIN_USER`, `GRAFANA_ADMIN_PASSWORD`를
제외하고 일치해야 합니다. 환경별 값 차이는
허용하며 값의 내용은 출력하지 않습니다.

공통 백엔드 설정은 `src/backend/.env.example`과 `docker/.env.example` 양쪽에
추가합니다. `make env-contract-check`는 어느 예제에 어떤 키가 빠졌는지 출력하고
불일치 시 실패합니다. 실제 `.env`와 프론트엔드 서브모듈 없이 실행할 수 있으며,
`make check`, `make ci`, GitHub CI의 백엔드 검사에도 포맷·린트와 같은 필수 검사로
연결되어 있습니다. 기존 env 명령도 동일한 비교를
수행하고, `docker-env-check`는 실제 배포 `.env`의 누락까지 검사합니다.
프론트엔드 `VITE_*` 설정은 별개입니다. 로컬 `.env`에만 추가한 키는 추가 키로
알림 처리되므로, 배포 반영을 강제할 공통 설정은 예제에도 선언해야 합니다.

sync는 기존 파일을 변경하기 전에 루트 `.env-backups/`에 시각이 포함된 백업을
만듭니다. 백업은 소유자만 읽을 수 있으며 Git과 Docker 빌드에서 제외됩니다.
변경이 없거나 파일을 새로 생성할 때는 백업하지 않습니다. 없는 파일은 예제로
생성합니다. 주석이나 순서만 바뀌어도 갱신과 백업을 수행하며, 변경이 없으면
파일을 다시 쓰지 않습니다.

`make docker-deploy`와 배포 스크립트 직접 실행 시 빌드·컨테이너 재생성 전에
`docker-env-check`를 실행합니다. 오류를 수정하거나 `make docker-env-sync` 후 추가된 설정을
검토하고 다시 배포하세요. 인증정보 유효성, 연결 상태, 실행 중인 컨테이너의
설정은 검사하지 않습니다. 이 검사로 인해 Docker 배포에도 `uv`가 필요합니다.

## Docker 배포

### DB·관측성 접근 설정

- 로컬 PostgreSQL은 `DB_USER`, `DB_PASSWORD`, `DB_NAME`으로 계정과 DB를
  초기화하며 앱도 같은 해석된 인증정보를 사용합니다. 기존 PostgreSQL 볼륨의
  계정은 유지되므로 `.env` 변경만으로 비밀번호가 바뀌지 않습니다. 기존 DB에서
  계정을 별도로 변경해야 하며, 비밀번호 변경을 위해 볼륨을 삭제하지 마세요.
- `REDIS_PASSWORD`가 비어 있지 않으면 로컬 Redis 서버·앱·healthcheck에 인증이
  함께 적용됩니다. 빈 값은 로컬 개발용으로 지원하며 배포 시 강한 비밀번호를
  설정하세요. PostgreSQL도 개발용 기본 비밀번호가 남아 있으므로 배포 시
  `DB_PASSWORD`를 설정해야 합니다.
- 백엔드가 DB 계정·비밀번호와 Redis 비밀번호를 URL 인코딩합니다. `.env`에는
  인코딩 전 원래 값을 입력합니다. `$`가 포함된 리터럴 값은 작은따옴표로 감싸
  Compose 변수 치환을 방지하세요.
- DB·Redis·Grafana·Prometheus·Tempo·OTLP의 호스트 포트는 `127.0.0.1`에만
  바인딩합니다. 컨테이너끼리는 기존 Compose 서비스 이름으로 통신합니다.
  외부 PC에서 접근하려면 SSH 터널 또는 별도로 설정한 프록시를 사용합니다.
  앱의 8000번 포트 공개 방식은 기존과 같습니다.
- Grafana 익명 접근은 비활성화합니다. `make docker-env-sync` 후 `docker/.env`의
  `GRAFANA_ADMIN_PASSWORD`를 지정하고 `make docker-observability-up`을 실행하세요.
  빈 비밀번호, `admin`, `CHANGE_ME*` 값이면 Grafana 시작을 거부합니다.
  `GRAFANA_ADMIN_USER` 기본값은 `admin`입니다. 계정 환경변수는 새 Grafana 볼륨
  초기화용이므로 기존 설치는 Grafana UI 또는 관리자 CLI에서 저장된 비밀번호를
  별도로 변경하고 `.env`도 그 값에 맞춰야 합니다.

설정은 컨테이너 재생성 시 반영됩니다. env sync/check는 키·배치만 검사하며,
기존 DB나 Grafana 계정 비밀번호를 자동 변경하지 않습니다.

1. 환경 준비:

```bash
make init
```

2. 앱 이미지 빌드:

```bash
make docker-build
```

3. 서비스 기동 (`docker/.env`에 따라 `app` + 선택적 `postgres/redis`):

```bash
make docker-up
```

4. 로그 확인:

```bash
make docker-logs DOCKER_SERVICE=app
```

5. 서비스 중지:

```bash
make docker-down
```

6. 원샷 배포 (빌드 + 재기동 + tar 내보내기):

```bash
make docker-deploy
```

7. 앱 이미지 tar 내보내기:

```bash
make docker-export
```

내보낸 이미지 파일은 `docker/artifacts/`에 저장됩니다.

## 빌드

백엔드:

```bash
make backend-format
make backend-test
```

프론트엔드:

```bash
make frontend-format
make frontend-build
```

브라우저 프론트엔드는 계속 기본 방식입니다. 선택형 로컬 데스크톱 개발은 다음 명령을 사용합니다.

```bash
cd src/frontend
npm run tauri:dev
```

또는 저장소 루트에서 실행할 수 있습니다. 실행기는 현재 셸에 Rust 경로가
반영되지 않은 경우 표준 설치 경로(`~/.cargo/bin`)를 자동으로 추가합니다.

```bash
make frontend-desktop-dev
```

## 공통 프론트 저장소

[B4React](https://github.com/Blueprint4Agent/B4React)는 `src/frontend` 서브모듈로 커밋을 고정합니다.
`git clone --recurse-submodules`로 복제하거나 기존 체크아웃에서 `make frontend-init`을 실행합니다.
`make init`, `make frontend-install`도 고정된 커밋을 초기화합니다.

- `make frontend-build`: 자체 `dist`만 생성합니다.
- `make frontend-package`: 빌드 후 백엔드 정적 경로로 복사합니다.
- `make build`: 백엔드 환경 준비와 통합 패키징입니다.
- `make contract-check`: 백엔드 스냅샷 최신성과 프론트 계약 일치를 검사합니다.
- `make frontend-api-check`: 생성 타입의 변경 누락을 검사합니다.

프론트 변경은 B4React PR에서 먼저 머지하고 부모 PR에서 커밋 포인터를 갱신합니다.
[서브모듈 통합 가이드](frontend-submodule.md)를 참고하세요. 한국어 프론트 문서는
`src/frontend/notes/ko/`에서 관리하며 기존 경로는 진입 링크입니다.
