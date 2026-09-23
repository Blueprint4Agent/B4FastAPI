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

## Docker 배포 (Bash 전용)

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
