# API 인증 정책 점검

[English](../api-authentication.md)

아래는 이 저장소의 현재 정책이며 업계 공통 규칙이 아닙니다.
앱 API 키(`X-API-Key`)와 백엔드의 Stripe 비밀 키는 별개입니다.
Stripe 키는 서버 환경설정에 사용하며 우리 API에 요청하는 사용자 인증용이 아닙니다.

| API (`/api/v1` 기준) | 앱 API 키 | 추가 조건 |
| --- | --- | --- |
| `GET /billing/config` | 가능 | 활성 계정 |
| `POST /billing/setup-sessions` | 가능 | 활성 계정 |
| `GET /billing/setup-sessions/{session_id}` | 가능 | 본인 등록 세션 |
| `GET /billing/payment-methods` | 가능 | 본인 결제수단만 |
| `POST /auth/me/deletion-code` | 불가, 401 | 로그인 세션, 로그인/이메일 활성화, 발송 제한 |
| `DELETE /auth/me` | 불가, 401 | 로그인, 이메일 일치, 일회용 코드, 마지막 관리자 보호 |
| `GET /auth/admin/users` | 가능 | 키 소유자가 현재 관리자여야 함, 아니면 403 |
| `GET /auth/admin/user-role-stats` | 가능 | 키 소유자가 현재 관리자여야 함, 아니면 403 |
| `GET/PATCH /auth/me` | 가능 | 활성 계정 |
| API 키 생성/조회/삭제/상태 변경 | 가능 | 본인 키만 |
| `GET /events/stream` | 가능 | 본인 이벤트 채널만 |
| `POST /auth/logout` | 가능 | 본인 갱신 세션 종료, 이미 발급된 access JWT는 정상 만료까지 유지 |

로그인 세션만 허용하는 API는 총 2개입니다. 관리자 API 2개는 키도 받지만 DB의 최신
사용자 역할을 별도로 검사합니다. 현재 키에는 `billing:read` 같은 API별 scope가 없습니다.
키로 프로필 수정, 본인의 다른 키 관리, 로그아웃도 할 수 있습니다. Billing도 같은 키 소유자 권한을 허용합니다. 계정 삭제는 bearer 전용을 유지합니다.

두 인증 방식을 허용하는 API에 bearer와 API 키를 함께 보내면 둘 다 유효하고 같은
사용자여야 합니다. 유효한 키가 있어도 bearer가 만료/오류이면 401, 사용자 불일치면
403입니다. bearer 전용 API는 X-API-Key를 검사하지 않습니다.

`POST /auth/refresh`는 별도의 갱신 토큰/세션 교환입니다. API 키나 access token만으로
실행되지 않고 JSON 또는 refresh 쿠키가 필요합니다. 가입/로그인, 이메일 인증/재설정,
OAuth도 비밀번호·일회용 토큰·state·기능 활성화 조건이 따로 있습니다.
Swagger에 인증 자물쇠가 없다고 이런 검증까지 없다는 뜻은 아닙니다.

Swagger의 OAuth2PasswordBearer에는 앱 이메일을 username, 앱 비밀번호를 password로
입력하여 `/auth/token`으로 로그인합니다. APIKeyHeader에는 앱 API 키를 넣습니다.
자물쇠는 인증 방식 표시이지 권한 검사 통과 표시가 아닙니다. APIKeyHeader를 등록해도
bearer 전용 API가 자동 인증되지는 않습니다. Swagger의 인증 방식 명세와 실제 guard는
일치하지만, 관리자 역할과 기능 활성화 조건은 별도입니다. 공통 `INVALID_TOKEN` 메시지는
현재 `Invalid refresh token`이어서 API 키만으로 bearer 전용 API를 요청해도 이 문구가
나올 수 있습니다. 이때는 인증 방식과 오류 코드를 함께 확인해야 합니다.

근거: `app/deps.py`, auth/billing/API-key/events 라우터, 실행 중 OpenAPI 생성 결과,
`tests/integration/api/v1/auth/test_api_auth_policy.py`. 격리된 SQLite에서 실제 앱 키를
발급하여 2개 차단 API와 Billing 12개 키 인증 분기, 관리자/일반 사용자 분기, 키 허용 기능, OpenAPI 목록을 검증합니다.
실제 운영 사용자나 계정은 변경하지 않았습니다. Billing 키 등록/조회와 소유자 격리도 통합 테스트합니다.
