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

1. 루트 가이드: `docs/ko/README.md`
2. 에이전트/워크플로 규칙: `docs/ko/AGENTS.md`
3. 배포 가이드: `docs/ko/DEPLOY.md`
4. 백엔드 엔지니어링 규칙: `docs/ko/backend/BACKEND.md`
5. 프론트엔드 엔지니어링 규칙: `docs/ko/frontend/FRONTEND.md`
6. 백엔드 빠른 가이드: `docs/ko/backend/README.md`
7. 프론트엔드 빠른 가이드: `docs/ko/frontend/README.md`

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
bash ./docker/scripts/init-env.sh
```

2. 백엔드 실행 (로컬 개발):

```bash
cd src/backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

3. 프론트엔드 실행 (로컬 개발):

```bash
cd src/frontend
npm ci
npm run dev
```

4. 접속:

- 백엔드 API 문서: `http://localhost:8000/docs`
- 프론트엔드 앱 (Vite): `http://localhost:5173`

## Docker 배포 (Bash 전용)

1. 환경 준비:

```bash
bash ./docker/scripts/init-env.sh
```

2. 앱 이미지 빌드:

```bash
bash ./docker/scripts/docker-build.sh
```

3. 서비스 기동 (`docker/.env`에 따라 `app` + 선택적 `postgres/redis`):

```bash
bash ./docker/scripts/docker-up.sh
```

4. 로그 확인:

```bash
bash ./docker/scripts/docker-logs.sh app
```

5. 서비스 중지:

```bash
bash ./docker/scripts/docker-down.sh
```

6. 원샷 배포 (빌드 + 재기동 + tar 내보내기):

```bash
bash ./docker/scripts/docker-deploy.sh
```

7. 앱 이미지 tar 내보내기:

```bash
bash ./docker/scripts/docker-export.sh
```

내보낸 이미지 파일은 `docker/artifacts/`에 저장됩니다.

## 빌드

백엔드:

```bash
cd src/backend
uv run ruff check . --fix
uv run ruff format .
```

프론트엔드:

```bash
cd src/frontend
npm run format
npm run build
```
