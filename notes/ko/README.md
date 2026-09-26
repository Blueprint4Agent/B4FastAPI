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
Tempo, Loki만 중지합니다. 앱, PostgreSQL, Redis는 계속 실행됩니다. 중지된 컨테이너와
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
키는 `scripts/env.py`에 명시한 Docker 전용 이미지·Compose 프로젝트·호스트 포트·수집 대상·
Grafana 로그인 설정을 제외하고 일치해야 합니다. 환경별 값 차이는
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

### 프로젝트 이름과 호스트 포트

컨테이너 이름은 Compose가 `<프로젝트>-<서비스>-1` 형태로 생성합니다.
기본 `COMPOSE_PROJECT_NAME=docker`는 기존 프로젝트의 볼륨 이름을 유지합니다.
새로 생성되는 컨테이너 이름은 `docker-postgres-1` 같은 형태이며, 기존 고정 이름의
컨테이너는 명시적으로 재생성하기 전까지 유지됩니다. 스크립트는 서비스 이름을
사용하므로 두 이름 방식 모두 지원합니다. 별도 설치는 `docker/.env`에서 고유한
프로젝트 이름과 사용하지 않는 호스트 포트를 지정합니다.

```dotenv
COMPOSE_PROJECT_NAME=b4fastapi
POSTGRES_HOST_PORT=5433
REDIS_HOST_PORT=6380
```

| 호스트 포트 설정 | 기본값 | 컨테이너 내부 포트 |
| --- | --- | --- |
| `APP_HOST_PORT` | 8000 | 8000 |
| `POSTGRES_HOST_PORT` | 5432 | 5432 |
| `REDIS_HOST_PORT` | 6379 | 6379 |
| `GRAFANA_HOST_PORT` | 3000 | 3000 |
| `PROMETHEUS_HOST_PORT` | 9090 | 9090 |
| `OTEL_GRPC_HOST_PORT` | 4317 | 4317 |
| `OTEL_HTTP_HOST_PORT` | 4318 | 4318 |

위 예제에서 호스트 백엔드의 `src/backend/.env`는 `DB_PORT=5433`,
`REDIS_PORT=6380`을 사용하고 Docker 앱은 `DB_PORT=5432`, `REDIS_PORT=6379`를
유지합니다. 전체 스택을 여러 개 실행하면 모든 공개 포트를 서로 다르게 설정하고,
빌드가 다를 경우 `APP_IMAGE` 태그도 구분하세요. 포트를 바꾸면 호스트 접근용
URL·CORS·로컬 OTLP 주소도 맞춰야 합니다. 호스트 개발 시 `PROMETHEUS_BACKEND_TARGET`을
실제 백엔드 포트에 맞춥니다. Docker 앱의 수집 대상은 `APP_HOST_PORT`와 관계없이
`app:8000`입니다.

`make docker-env-sync`로 설정 키를 추가합니다. 프로젝트 이름을 바꾸면 별도
컨테이너·볼륨이 생성되며 기존 데이터가 자동 이전되지는 않습니다. 현재 설치는
의도적으로 이전할 때까지 `docker`를 유지하세요. 기존 DB·Redis의 호스트 포트
변경은 아래 안내대로 해당 서비스를 명시적으로 재생성해야 적용됩니다.
`docker-up`은 기존 인프라를 유지합니다.

### DB·관측성 접근 설정

#### Loki 애플리케이션 로그

로그 경로는 `Python logging -> OTLP/gRPC -> Collector batch -> OTLP/HTTP -> Loki`입니다.
[네이티브 Loki OTLP 엔드포인트](https://grafana.com/docs/loki/latest/send-data/otel/)를
기존 Collector에 연결하므로 Docker 소켓이나 별도 로그 에이전트가 필요하지 않습니다.

1. 개발은 `make env-sync`, 배포는 `make docker-env-sync`로 새 설정을 추가합니다.
   기존 값은 유지되며 백업이 생성됩니다.
2. 호스트 개발은 `src/backend/.env`, Docker 앱은 `docker/.env`에서
   `LOGS_ENABLED=true`로 설정합니다. 기본값은 false이며 `TRACING_ENABLED`와 독립적입니다.
3. `OTEL_EXPORTER_OTLP_ENDPOINT`는 호스트에서 `http://localhost:4317`,
   Docker에서 `http://otel-collector:4317`입니다. 호스트 포트를 바꿨다면 함께 맞춥니다.
4. `make docker-observability-up`으로 실행합니다. 기존 설치에서는 마운트된
   Collector 설정과 Grafana 데이터소스를 다시 읽도록 재시작합니다.

   ```bash
   docker compose -f docker/docker-compose.yml --env-file docker/.env --profile observability restart otel-collector grafana
   ```

5. 개발 백엔드를 재시작(`make backend-dev`)하거나 Docker 앱을 다시 빌드·생성
   (`make docker-deploy`)하여 새 의존성과 설정을 적용합니다.
6. Grafana **Explore → Loki**에서 최근 시간 범위를 선택하고 조회합니다.

   ```logql
   {service_name="blueprint4fastapi-backend"}
   ```

설정 이후 `uvicorn.app` 하위 애플리케이션·워커 로그, Uvicorn 서버 및 접근 로그를
`LOG_LEVEL`에 맞춰 수집합니다. 콘솔 출력도 유지합니다.
PostgreSQL·Redis·컨테이너 stdout이나 임의의 루트 로거는 수집하지 않습니다.
요청·작업 ID는 인덱스 라벨이 아닌 구조화 메타데이터이며
`| request_id="..."`, `| task_id="..."`로 필터링합니다. 활성 OTel 스팬은 네이티브
트레이스 연결을 제공하지만 헤더·작업의 대체 ID가 Tempo 저장을 보장하지는 않습니다.
SDK 배치는 정상 프로세스 종료 시 전송됩니다. 강제 종료, 큐 초과, Collector 장기
장애 시 로그가 유실될 수 있으므로 영속적인 감사 로그 용도는 아닙니다.

Loki 시작 전 일회성 `loki-init` 서비스가 볼륨 최상위 디렉터리의 소유권을
Loki 이미지 사용자 UID/GID 10001로 맞춥니다. `loki-init`의 `Exited (0)`는 정상입니다.
초기 구성에서 root 소유로 생성된 볼륨도 기존 데이터를 유지하며 보정합니다.
Loki 본체는 이미지의 일반 사용자로 실행합니다.

Loki는 단일 인스턴스이며 `loki_data` 볼륨에 저장하고 7일 보존합니다
(Compactor 삭제는 비동기). 인증 없는 API는 호스트 포트를 공개하지 않고
Compose 네트워크의 `loki:3100`에서만 사용하며 Grafana 데이터소스를 통해 조회합니다.
이 구성은 단일 호스트용이며 공용 운영 환경에서는 해당 환경에 맞는 저장소·접근 정책이 필요합니다.

#### Collector 트레이스 배치

트레이스 파이프라인은 `OTLP receiver -> batch processor -> Tempo/debug exporters`입니다.
Collector 0.114.0 기본값인 200ms 타임아웃과 8192개 스팬 전송 기준을 사용합니다.
8192는 최대 배치 크기가 아닌 전송을 시작하는 기준입니다. 백엔드 SDK의 기존
`BatchSpanProcessor`와 별개로 Collector에서 수신한 스팬을 모아 전송합니다.
[배치 프로세서 문서](https://github.com/open-telemetry/opentelemetry-collector/blob/v0.114.0/processor/batchprocessor/README.md)를 참고하세요.

마운트된 설정 파일 변경은 실행 중인 Collector를 재시작해야 반영됩니다.

```bash
docker compose -f docker/docker-compose.yml --env-file docker/.env --profile observability restart otel-collector
```

#### Prometheus 수집 대상과 공통 네트워크

앱·Prometheus·Grafana 등 Compose 서비스는 이미 같은
`<COMPOSE_PROJECT_NAME>_default` 네트워크를 사용합니다. 앱과 관측성 명령에서
같은 프로젝트 이름을 유지하면 되며 별도 외부 공통 네트워크는 필요하지 않습니다.

`make docker-env-sync` 후 `docker/.env`에 수집 대상 하나를 지정합니다.

| 백엔드 실행 방식 | PROMETHEUS_BACKEND_TARGET |
| --- | --- |
| 호스트에서 `make backend-dev` (기본 포트) | `host.docker.internal:8000` |
| 호스트 백엔드를 8001번 포트로 실행 | `host.docker.internal:8001` |
| 같은 Compose 프로젝트에서 `make docker-up` | `app:8000` |

설정 후 `make docker-observability-up`으로 반영합니다. 백엔드가 사용하는 env에서
`METRICS_ENABLED=true`도 설정하고 필요하면 백엔드를 재시작·재생성하세요.
호스트 백엔드는 Docker에서 접근 가능한 주소에 바인딩해야 합니다.
`make backend-dev` 기본값은 `0.0.0.0`이며 Linux 호스트 접근도 host-gateway
매핑으로 지원합니다. 대상에는 host:port만 입력하며 `/metrics` 경로는 별도 설정되어
있습니다. Prometheus는 컨테이너 시작 시 설정 파일을 생성·검사합니다.
기존 대시보드·이력 호환성을 위해 두 모드 모두 `b4fastapi-backend-local` job
라벨을 유지합니다. Prometheus의 `/targets` 화면에서 수집 상태를 확인할 수 있습니다.

#### DB 드라이버

`DB_NAME`의 의미는 드라이버에 따라 다릅니다. DB 전환 시 두 값을 함께 변경합니다.

| 실행 환경 | DB_DRIVER | DB_NAME | DB_HOST |
| --- | --- | --- | --- |
| 로컬 SQLite (개발 기본값) | `sqlite+aiosqlite` | `template.db` (파일명) | 사용 안 함 |
| 호스트 백엔드 + Docker PostgreSQL | `postgresql+asyncpg` | `template` (DB 이름) | `localhost` |
| Docker 앱 + Docker PostgreSQL | `postgresql+asyncpg` | `template` (DB 이름) | `postgres` |

PostgreSQL에는 실제 존재하는 DB 이름과 일치하는 인증정보를 지정합니다. 예제의
`template` DB는 로컬 DB 볼륨을 처음 초기화할 때 생성됩니다. `env-sync`는 기존
값을 보존하므로 드라이버를 바꿔도 SQLite 파일명을 PostgreSQL DB 이름으로 자동
변경하지 않습니다. env 검사는 DB 존재 여부를 확인하지 않습니다. 전환 후
`database "template.db" does not exist` 오류가 나면 SQLite용 이름이 남았는지
확인하세요.

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
- DB·Redis·Grafana·Prometheus·OTLP의 호스트 포트는 `127.0.0.1`에만
  바인딩합니다. 컨테이너끼리는 기존 Compose 서비스 이름으로 통신합니다.
  외부 PC에서 접근하려면 SSH 터널 또는 별도로 설정한 프록시를 사용합니다.
  앱은 기존처럼 모든 호스트 인터페이스에 공개하며 `APP_HOST_PORT`(기본 8000)를 사용합니다.
- Tempo와 Loki는 호스트 포트를 공개하지 않습니다. Grafana는 Compose 네트워크의
  `tempo:3200`, `loki:3100`으로 조회하고, Collector는 `tempo:4317`로 트레이스,
  `loki:3100/otlp`로 로그를 전달합니다. 기존 `docker/.env`의 `TEMPO_HOST_PORT`는
  더 이상 사용하지 않으므로 삭제할 수 있습니다.
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

`uv`와 `up --wait --wait-timeout`을 지원하는 Docker Compose가 필요합니다.
인프라 선택은 Compose가 해석한 앱 환경변수를 기준으로 하므로 따옴표·주석·변수
치환·서비스 환경변수 우선순위를 반영합니다. 기존 PostgreSQL·Redis 컨테이너는
`--no-recreate`로 보존하고, 없으면 생성하며 중지 상태면 시작합니다. 각 기동 단계는
기본 120초까지 기다립니다 (`HEALTH_TIMEOUT_SECONDS=180 make docker-up`으로 변경).
앱 healthcheck는 DB와 Redis 연결을 확인하는 `/health/ready`를 호출합니다.
준비 상태에 도달하지 못하면 실패하며 자동 롤백은 수행하지 않습니다.

로컬 인프라의 인증정보나 설정을 의도적으로 바꿀 때는 해당 서비스만 명시적으로
재생성한 뒤 앱도 재생성하거나 재배포합니다.

```bash
docker compose -f docker/docker-compose.yml --env-file docker/.env up -d --no-deps --force-recreate postgres
docker compose -f docker/docker-compose.yml --env-file docker/.env up -d --no-deps --force-recreate redis
```

PostgreSQL 재생성만으로 기존 데이터 볼륨에 저장된 계정 비밀번호는 바뀌지 않습니다.

4. 로그 확인:

```bash
make docker-logs DOCKER_SERVICE=app
```

5. 서비스 중지:

```bash
make docker-down
```

6. 원샷 배포 (환경 검사 + 빌드 + 앱 재생성 + 준비 대기 + tar 내보내기):

```bash
make docker-deploy
```

앱만 강제 재생성하며 기존 로컬 DB·Redis 컨테이너의 설정은 유지합니다.
준비 확인에 실패하면 이미지 내보내기 전에 배포가 중단됩니다. 이미지 내보내기도
`.env`의 `APP_IMAGE`를 따로 파싱하지 않고 Compose가 해석한 앱 이미지명을 사용해
빌드와 동일한 기준을 따릅니다.

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

## 작업 절차와 PR 검사

가이드와 작업 상태 확인 → 작업 브랜치 생성 → [워크로그 초안](../../.github/WORKLOG_TEMPLATE.md)
작성 → 구현 → Make 검사 → 결과 기록·스테이징 → Git 규칙 검사 → 커밋·PR 순으로 진행합니다.
워크로그에는 설계, 검증 계획, 관련 루프와 실제 검증 결과를 기록합니다.

`make git-governance-check`는 COMMIT_TITLE을 전달하면 스테이징된 파일과
COMMIT_BODY_FILE을 검사하고, 전달하지 않으면 HEAD 커밋을 검사합니다.
PR_TITLE과 PR_BODY_FILE은 함께 전달합니다. 미추적 워크로그는 인정하지 않습니다.
PR CI는 실제 커밋 범위의 각 일반 커밋과 워크로그 제목·필수 내용을 검사하며,
PR 제목·본문을 수정해도 다시 실행됩니다. 브랜치 통합용 merge commit은 제외합니다.
Python 3 표준 라이브러리만 사용합니다. 구체적인 절차는 [AGENTS.md](../../AGENTS.md)를 참고하세요.

main은 PR과 Git governance 및 저장소별 코드 검사를 요구합니다. 1인 작업을 지원해
필수 승인 수는 0이며, 자동 검사는 사람의 설계 리뷰를 의미하지 않습니다.
워크로그를 작업 시작 시 작성하는지는 절차로 관리하고, CI는 커밋된 기록을 검증합니다.

## 아키텍처 검사

`make architecture-check`로 문서화된 계층 의존성 규칙을 검사합니다.
`make check`와 필수 PR CI에서도 실행하며 위반 파일·줄 번호를 출력합니다.
백엔드만 검사하려면 `make backend-architecture-check`, 프론트만 검사하려면
`make frontend-architecture-check`를 사용합니다. Router의 직접 DB 의존성과 하위
계층의 Router/app.main 참조, UI의 직접 API 의존성과 컴포넌트의 도메인 훅 의존성을
검사합니다. 스키마·Enum 및 명시적인 타입 전용 import는 허용합니다.
정확한 검사 범위와 한계는 각 도메인 가이드에 기록합니다.

## API Key 정합성

API Key 화면 갱신 알림은 최선 노력 방식입니다. DB 생성·삭제·상태 변경이 커밋된 뒤
Redis·OS·시간 초과로 알림 전송이 실패해도 경고를 기록하고 성공 응답을 유지합니다.
알림 대기는 최대 2초이며 취소와 프로그래밍 오류는 전파합니다. 영속 이벤트
outbox나 재전송 기능을 제공하는 것은 아닙니다.

프론트 useApiKeys 훅이 목록·로딩·오류·변경 상태를 소유합니다. HTTP와 SSE는 같은
ID 기준 갱신을 사용하고, 이벤트·변경 완료 후 서버 목록으로 재동기화합니다.
연결·재연결, 개발자 탭 진입, 데스크톱 연결 복구 시 재조회하며 오래된 목록 응답과
이전 계정의 응답은 무시합니다. 모달·입력·일회성 키는 SettingsPage에 남기고,
탭 변경으로 진행 중인 생성 결과를 버리지 않습니다. 백그라운드 재조회 중 기존
목록을 유지합니다. API 스키마는 바뀌지 않습니다.
