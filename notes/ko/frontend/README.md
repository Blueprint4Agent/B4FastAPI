# 프론트엔드 빠른 가이드

이 문서는 `src/frontend` 작업자를 위한 가이드입니다.
전체 엔지니어링 제약은 `src/frontend/FRONTEND.md`를 따르세요.

## 1) 설정

```bash
cd src/frontend
npm ci
```

## 2) 개발 서버 실행

```bash
cd src/frontend
npm run dev
```

기본 로컬 URL:

- `http://localhost:5173`

브라우저 실행은 계속 기본 프론트엔드 방식입니다. 같은 React 애플리케이션을 선택형
Tauri 데스크톱 셸에서 실행하려면 다음 명령을 사용합니다.

```bash
cd src/frontend
npm run tauri:dev
```

Rust가 `~/.cargo/bin`에 설치되어 있지만 현재 셸이 해당 경로를 불러오지 않은
경우 실행기가 명령 PATH에 자동으로 추가합니다. 저장소 루트에서는 동일하게
`make frontend-desktop-dev`를 사용할 수 있습니다.

Tauri 개발에는 Rust toolchain이 필요합니다. 로컬 데스크톱 셸은 기본적으로
`http://localhost:8000` API에 연결하며, 다른 API가 필요하면 `VITE_API_BASE_URL`을 설정합니다.
현재 데스크톱 셸은 온라인 우선입니다. 오프라인에서도 정적 UI asset은 열리지만 인증,
API 키 관리, 실시간 이벤트 및 서버 데이터에는 FastAPI 연결이 필요합니다. 오프라인 데이터
캐시와 재동기화는 셸에 포함되지 않은 별도 기능입니다.
Tauri에서는 네이티브 창 컨트롤이 랜딩, 인증 및 앱 내부 Nav와 같은 타이틀바 영역을
공유합니다. 브라우저 프론트엔드는 기존 탐색 레이아웃을 유지합니다.

API base URL 동작:

- `VITE_API_BASE_URL`이 설정되어 있으면 해당 값을 사용합니다. 로컬 루프백 별칭
  (`localhost`, `127.0.0.1`, `::1`)은 인증 쿠키가 same-site로 유지되도록 현재 프론트 호스트에 맞춥니다.
- 미설정 상태에서 현재 포트가 `5173`(Vite dev)이면 기본값으로 `http(s)://<current-host>:8000`을 사용합니다.
- 그 외에는 현재 페이지 origin(same-origin)을 기본값으로 사용하며, 백엔드 static 서빙 모드에 유용합니다.

## 3) API 타입 생성

프론트 API 계약은 백엔드 OpenAPI에서 생성됩니다.

```bash
cd src/frontend
npm run generate:api
```

서버 선택적 동기화 (백엔드가 없어도 기존 생성 파일 사용):

```bash
cd src/frontend
npm run api:sync
```

생성 대상:

- `src/api/generated/openapi.ts`

## 4) 포맷 / 체크

```bash
cd src/frontend
npm run format
npm run format:check
```

## 5) 테스트

```bash
cd src/frontend
npm run test
```

레이어별 실행:

```bash
cd src/frontend
npm run test:unit
npm run test:component
npm run test:integration
```

전체 매트릭스 실행 (unit -> component -> integration -> e2e):

```bash
cd src/frontend
npm run test:all
```

E2E 스모크:

```bash
cd src/frontend
npm run test:e2e
```

## 6) 빌드

```bash
cd src/frontend
npm run build
```

FastAPI static 경로로 복사하지 않고 데스크톱 셸용 공용 웹 asset만 빌드합니다.

```bash
npm run build:desktop
```

선택적 API 계약 갱신 + 빌드:

```bash
cd src/frontend
npm run build:sync
```

백엔드에서 엄격 API 계약 갱신 + 빌드:

```bash
cd src/frontend
npm run build:strict
```

참고:

- `npm run build`는 기본적으로 서버 비의존입니다(OpenAPI fetch 없음).
- `npm run build:sync`는 빌드 전 선택적 OpenAPI 갱신을 시도하며, fetch 실패 시 기존 생성 파일로 fallback합니다.
- `npm run build:strict`는 `localhost:8000`의 OpenAPI 갱신 성공이 선행되어야 빌드됩니다.

## 7) 핵심 프론트엔드 규칙 (요약)

- API 흐름: `generated -> api/<domain> -> hooks/api/<domain> -> pages`
- 도메인 세트 규칙: `<domain>Api.ts` + `<domain>Error.ts` + `use<Domain>Api.ts`는 1:1:1 유지
- 인증이 필요한 실시간 스트림(`/api/v1/events/stream`)은 bearer 헤더 전달을 위해 `api/events` 도메인에서 fetch 스트리밍으로 처리
- 도메인 hook 호출은 feature component가 아니라 page 레이어에서 수행
- feature component는 state/actions를 props로 전달받아 사용
- 재사용 컴포넌트는 `src/components/ui/*`(카테고리 폴더) 배치
- 도메인 전용 컴포넌트는 `src/components/features/<domain>/*` 배치
- 모든 CSS는 `src/styles/app.css`에서 관리
- 신규 재사용 UI 컴포넌트는 `src/pages/main/ShowCasePage.tsx`에 반드시 전시

## 8) 커밋 전 체크

```bash
cd src/frontend
npm run format
npm run format:check
npm run test
npx tsc --noEmit
npm run build
```
