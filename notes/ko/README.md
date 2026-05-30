# Blueprint4FastAPI

Blueprint4FastAPI는 다음 구성을 갖춘 풀스택 템플릿입니다.

- 백엔드: FastAPI + SQLAlchemy + Alembic + Redis
- 프론트엔드: React + TypeScript + OpenAPI 기반 API 타입 생성
- 모놀리식 정적 서빙 지원 (프론트 빌드를 백엔드 static 경로로 복사)

## 문서 시작점

1. 에이전트/워크플로 규칙: `AGENTS.md`
2. 배포 가이드: `DEPLOY.md`
3. 백엔드 엔지니어링 규칙: `src/backend/BACKEND.md`
4. 프론트엔드 엔지니어링 규칙: `src/frontend/FRONTEND.md`
5. 백엔드 빠른 가이드: `src/backend/README.md`
6. 프론트엔드 빠른 가이드: `src/frontend/README.md`

한국어 문서:

1. 루트 가이드: `notes/ko/README.md`
2. 에이전트/워크플로 규칙: `notes/ko/AGENTS.md`
3. 배포 가이드: `notes/ko/DEPLOY.md`
4. 백엔드 엔지니어링 규칙: `notes/ko/backend/BACKEND.md`
5. 프론트엔드 엔지니어링 규칙: `notes/ko/frontend/FRONTEND.md`
6. 백엔드 빠른 가이드: `notes/ko/backend/README.md`
7. 프론트엔드 빠른 가이드: `notes/ko/frontend/README.md`

## 저장소 구조

```text
src/
  backend/
  frontend/
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
