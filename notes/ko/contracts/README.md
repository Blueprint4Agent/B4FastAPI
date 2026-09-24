# B4 API 계약 기준

공통 React 프론트와 대체 백엔드 구현을 위한 현재 HTTP 계약입니다.
기준 파일은 [`contracts/openapi.json`](../../../contracts/openapi.json)이며,
영문 상세 문서는 [`contracts/README.md`](../../../contracts/README.md)입니다.

## 계약 관리와 생성

전환 단계의 작성 원본은 FastAPI 라우터·모델입니다. JSON 기준 파일과
프론트 생성 타입은 직접 수정하지 않습니다. OpenAPI 3.1, API 버전 `0.1.0`을
사용하며 추출 시 서버 시작, DB/Redis 연결, 마이그레이션은 실행하지 않습니다.
배포 이름에 따른 차이를 없애기 위해 추출 문서 제목은 `B4 API`로 고정합니다.

루트에서 다음 순서로 실행합니다.

`make contract-export`는 부모의 제공자 계약을 갱신합니다. 검토된 계약을 B4React PR에서
출처·생성 타입·호출부와 함께 도입하고 머지한 다음 부모 포인터를 갱신합니다.
[변경 순서](../frontend-submodule.md)를 참고하세요.
`make frontend-api-generate`는 자식의 자체 계약만 사용합니다.

`make check test build`로 검증합니다. `contract-check`는 백엔드 내보내기와
프론트 계약의 의미상 일치를 검사하고 `frontend-api-check`는 생성 타입의 변경 누락을 검사합니다.
이 검사는 다른 백엔드 구현의 런타임 호환성을 보장하지 않습니다.

## HTTP와 오류

- 도메인 API는 `/api/v1`이며 `/config`, `/health/live`, `/health/ready`도
  프론트가 사용하는 공개 계약입니다. JSON의 snake_case, 정수, 날짜·시간 문자열,
  필드별 생략/null 차이를 유지합니다.
- 보호된 API는 Bearer JWT 또는 `X-API-Key`를 받습니다. 둘 다 주어진 경우
  잘못된 Bearer를 무시하지 않으며 인증된 사용자가 서로 같아야 합니다.
  API Key는 만료·비활성 여부를 검사하고 사용량을 기록합니다.
- 도메인 오류: `{ detail: { error, message, details? } }`.
  동일 상태 코드의 인증/API Key 오류는 `anyOf`로 보존합니다.
- 입력 검증 실패: 422, `HTTPValidationError` 형식.
- 응답 시작 전 예상하지 못한 오류: 500, `{ error: "INTERNAL_ERROR", message }`.
  도메인 500의 `detail` 형식과 구분하여 현재 동작을 그대로 기록합니다.
  없는 경로·메서드 같은 프레임워크 오류는 도메인 오류 계약 밖입니다.
- 요청 추적 헤더는 `X-Request-ID`, `X-Trace-ID`입니다.
  FastAPI는 유효한 활성 OpenTelemetry trace ID를 `X-Trace-ID`와 로그에 사용합니다.
  인바운드 `X-Trace-ID`는 활성 span을 덮어쓰지 않습니다. 활성 span이 없으면 기존의
  traceparent / X-Trace-ID / 생성 ID 순서를 사용합니다. 샘플링 제외 등으로 인해
  상관관계 ID가 있어도 trace가 내보내지지 않을 수 있습니다.

## 인증·쿠키·OAuth

- `/api/v1/auth/login`은 JSON을 받아 토큰·사용자를 반환하고
  `template_refresh_token`, `template_refresh_sid` 쿠키를 각각 설정합니다.
  SID는 응답 JSON이 아닌 쿠키로 전달됩니다.
- 쿠키는 HttpOnly, Path=/, 명시적 Domain 없음입니다. HTTPS는 Secure와
  SameSite=None, HTTP는 SameSite=Lax입니다. HTTPS 판정에 첫 번째
  X-Forwarded-Proto 값이 사용되므로 배포 프록시가 해당 헤더를 관리해야 합니다.
- remember_me=true일 때만 브라우저의 영속 만료를 설정합니다. 서버의 세션 TTL은
  두 경우 모두 REFRESH_TOKEN_EXPIRE_DAYS입니다.
- refresh는 선택적인 JSON refresh_token, session_id, user_id를 받습니다.
  비어 있지 않은 토큰/SID 필드는 쿠키보다 우선하며 user_id 생략 시 세션에서
  조회합니다. 브라우저는 credentials와 함께 `{}`를 보낼 수 있습니다.
- refresh 성공은 access token 발급과 기존 refresh 세션 TTL 연장입니다.
  **refresh token 값과 SID는 유지되므로 토큰 회전이 아닙니다.**
- logout은 해당 사용자의 모든 refresh 세션을 무효화하고 두 쿠키를 만료시킵니다.
  이미 발급된 access JWT는 만료 전까지 유효합니다.
- `/auth/token`은 OAuth2 폼 기반 도구용이며 브라우저 refresh 쿠키를 설정하지
  않습니다. 브라우저 로그인은 `/auth/login`을 사용합니다.
- OAuth 시작은 provider로 307 리다이렉트합니다. 콜백 성공은 APP_BASE_URL의
  성공 경로로 307 이동하며 영속 refresh 쿠키를 설정합니다. provider·도메인 실패는
  실패 경로로 error 및 경우에 따라 message 쿼리를 전달합니다. 핸들러 진입 전
  잘못된 provider/query 검증은 422, 예상하지 못한 실패는 500일 수 있습니다.
- CORS는 실제 웹/Tauri origin과 credentials를 허용해야 하며 콜백 URL은
  프록시 외부의 공개 scheme/host를 유지해야 합니다.

## 설정·readiness

- `/config`는 로그인·이메일·OAuth 기능 설정을 반환합니다. 로그인 비활성 시
  시작 과정에서 bootstrap 사용자·토큰이 제공될 수 있습니다.
  설정 조회 실패를 login_enabled=false로 해석하면 안 됩니다.
- `/health/live`: 200, `{ status: "ok" }`.
- `/health/ready`: 정상은 200/ok, 의존 서비스 장애는 503/degraded입니다.
  현재 checks에는 database/redis의 ok 또는 failed가 포함됩니다.
  대체 백엔드도 Tauri가 사용하는 이 공개 응답을 제공해야 합니다.

## SSE

- `/api/v1/events/stream`은 JSON 문서가 아닌 text/event-stream입니다.
  프론트는 Authorization과 credentials를 포함한 fetch 스트리밍을 사용합니다.
- 프레임의 id, event, data 중 data에 JSON 이벤트를 담습니다. 연결 프레임은
  retry 밀리초 값도 포함합니다. heartbeat는 ping입니다.
- 이벤트 JSON은 id, type, version(현재 v1), ts, payload를 포함합니다.
  OpenAPI의 x-sse-event-schema가 RealtimeStreamEvent를 참조하며 HTTP 본문
  자체는 문자열 스트림으로 표현됩니다.
- connected payload: user_id, channel. channel은 내부 구조를 해석하지 않습니다.
- ping payload: 현재 빈 객체.
- api_key.created / api_key.status_updated / api_key.deleted payload:
  `{ api_key: APIKeyResponse }`. 원본 API Key 비밀값은 전송하지 않습니다.
- RealtimeEvent는 일반 봉투, RealtimeStreamEvent/APIKeyEvent는 알려진 이벤트의
  타입입니다. 프론트는 생성 타입을 사용하며 알 수 없는 이벤트는 무시할 수 있습니다.
- pub/sub 기반으로 이벤트 재생·정확히 한 번 전달은 보장하지 않습니다.
  Last-Event-ID는 진단 목적으로만 수신합니다. 스트림 시작 후 장애는 JSON 상태
  응답 대신 연결 종료로 나타납니다.

## 후속 작업과 현재 한계

- 브라우저 SSE 재연결 시 REST 최신 상태 재조회는 아직 보장되지 않습니다.
  연결 단절 중 변경을 놓칠 수 있으며 데스크톱 세션 복구만으로 해결되지 않습니다.
- refresh 실패 시 라우터가 쿠키 삭제를 시도하지만 전역 예외 핸들러가 별도 응답을
  생성하므로 실패 응답의 쿠키 삭제는 현재 보장되지 않습니다.
- TypeScript 생성은 런타임 검증이 아닙니다. 기존 API Key 이벤트 소비자는
  수신 레코드를 부분적으로만 검사합니다.
- Spring Boot 제공자 테스트,
  DB 이전과 운영 중 스택 교체는 이후 단계입니다.
