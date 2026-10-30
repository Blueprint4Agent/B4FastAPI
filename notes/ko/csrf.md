# 쿠키 기반 refresh CSRF 보호

브라우저는 Redis refresh 세션에 연결된 CSRF 토큰을 사용합니다.

1. 쿠키와 `X-CSRF-Bootstrap: 1` 헤더로 `GET /api/v1/auth/csrf`를 호출합니다.
2. 응답의 `csrf_token`을 `X-CSRF-Token` 헤더에 넣어 `POST /api/v1/auth/refresh`를 호출합니다.
3. 토큰 누락·변조·다른 세션의 토큰은 갱신 전에 `403 CSRF_INVALID`로 거부합니다.

두 성공 응답은 `Cache-Control: no-store`를 사용합니다. 토큰은 로그나 영구 저장소에
기록하지 않습니다. 프론트엔드는 새로고침·OAuth 복귀·데스크톱 복구를 포함하여
갱신마다 토큰을 가져옵니다. 갱신당 요청 하나가 추가되며 별도 세션 저장소나 재시도
루프는 없습니다. 토큰 조회 실패 시 refresh를 보내지 않습니다.

조회 경로는 HttpOnly refresh 쿠키 두 개를 검증하고 사용자 정의 헤더를 요구하여
교차 출처 브라우저 요청에 CORS preflight를 적용합니다. `CORS_ORIGINS`에는 신뢰하는
프론트엔드 출처만 허용하세요. 임의 출처나 신뢰하지 않는 하위 도메인을 허용하면 안 됩니다.
별도 사이트 배포를 위해 HTTPS 쿠키는 `Secure; HttpOnly; SameSite=None`을 유지합니다.
토큰 응답 보호는 브라우저 동일 출처/CORS 정책에 의존합니다. HttpOnly만으로 CSRF를
막을 수 없으며 CSRF 토큰이 XSS를 방어하지는 않습니다.

무작위 256비트 토큰을 `refresh_csrf:<session_id>`에 저장하고 Redis SET NX로 동시 조회가
같은 토큰을 받도록 합니다. 기존 세션도 수명을 늘리지 않고 최초 조회 때 발급합니다.
갱신 시 세션과 토큰 TTL을 연장하고 로그아웃·계정 폐기 시 함께 삭제합니다.
SQL 마이그레이션이나 강제 로그아웃은 필요하지 않습니다.

JSON에 `refresh_token`과 `session_id`를 모두 직접 제공하는 클라이언트만 검증을 면제합니다.
하나라도 쿠키로 보충하면 CSRF 토큰이 필요합니다. Bearer/API-key 인증은 그대로 유지합니다.
비밀번호 로그인 CSRF 보호나 OAuth state의 브라우저 바인딩은 이번 변경에 포함되지 않습니다.

백엔드와 대응하는 프론트엔드를 함께 배포해야 합니다. 이전 브라우저 클라이언트는 갱신 시
403을 받습니다. Origin 검증과 로그인 CSRF 검토는 별도 후속 범위이며 구현 완료로 간주하지 않습니다.

[English](../csrf.md)
