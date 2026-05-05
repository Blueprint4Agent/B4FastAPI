# 백엔드 테스트 엔지니어링 가이드

이 문서는 `src/backend`의 테스트 아키텍처와 작업 규칙을 정의합니다.
테스트를 추가/변경할 때 이 가이드를 따르세요.

## 0) 범위와 우선순위

- 범위: `src/backend/tests` 하위 전체
- 백엔드 테스트 작업 전 읽기 순서:
1. 루트 `AGENTS.md`
2. `src/backend/BACKEND.md`
3. 이 문서 (`src/backend/TEST.md`)
- 충돌 시 우선순위:
1. 루트 `AGENTS.md`
2. `src/backend/BACKEND.md`
3. 이 문서

## 1) 테스트 전략 (De Facto, 프로젝트 적응형)

권장 피라미드:
1. Smoke: 앱 부팅 및 핵심 라우트 가용성
2. API Contract: dependency override 기반 router 요청/응답/인증 계약
3. Unit: 모킹된 의존성 기반 service/util 로직
4. Integration: 격리된 테스트 데이터 기반 DB/Redis/외부 연동
5. E2E: 실행 환경에서 전체 시스템 검증

현재 구현된 기준선:
1. 스모크 테스트 (`tests/test_smoke.py`)
2. 도메인별 API 계약 테스트 (`tests/api/v1/<domain>/test_*_api.py`)
3. 도메인별 통합 테스트 (`tests/integration/api/v1/<domain>/test_*_integration.py`)
4. 시드 기반 full-system 통합 시나리오 (`tests/integration/scenarios/test_full_system_scenario.py`)

## 2) 현재 디렉터리 레이아웃

```text
src/backend/tests/
  conftest.py
  test_smoke.py
  api/
    v1/
      auth/
        test_auth_api.py
      api_key/
        test_api_key_api.py
      events/
        test_events_api.py
  integration/
    api/v1/
      auth/
        test_auth_integration.py
      api_key/
        test_api_key_integration.py
    scenarios/
      test_full_system_scenario.py
```

확장 예정 레이아웃:

```text
src/backend/tests/
  unit/
    services/
    utils/
```

## 3) 핵심 원칙

1. 테스트에서 `Router -> Service` 경계를 명확히 유지
2. 빠르고 결정적인 테스트를 우선 (smoke + API contract)
3. router 테스트에서는 `dependency_overrides`로 서비스/인증 의존성을 대체
4. smoke/API contract 테스트에서 실제 외부 I/O 사용 금지
5. 동작이 DB/Redis 트랜잭션 의미론에 의존하면 integration 테스트 추가

## 4) 스모크 테스트 규칙

- 목적: 애플리케이션 부팅 및 핵심 라우트 가용성 확인
- 현재 엔드포인트 계약: `GET /ping -> 200 {"status":"ok","message":"pong"}`
- 파일: `tests/test_smoke.py`
- 스모크 테스트는 최소한으로 유지하고 항상 빨라야 함

## 5) API 계약 테스트 규칙 (현재 메인 하네스)

각 API 도메인에 대해:
1. `tests/api/v1/<domain>/test_<domain>_api.py` 생성
2. 작은 테스트 앱을 구성하고 대상 router만 include
3. 의존성 override 적용 (`AuthService`, `APIKeyService`, `get_current_user` 등)
4. status code + 핵심 응답 계약 검증

도메인별 필수 최소 커버리지:
1. 성공 케이스 (200/201)
2. 인증 실패 케이스 (보호 라우트일 때 401)
3. 요청 검증 실패 (입력 불일치 시 422)

이 코드베이스 참고:
1. router 테스트는 실제 repository가 아닌 fake service 사용
2. DB/Redis 런타임 상태와 독립적으로 테스트 유지 가능
3. API contract 테스트는 운영형 시드 데이터가 아닌 최소 계약 payload를 사용

## 6) Fixture와 재사용

- 공통 fixture는 `tests/conftest.py`에 배치
- API contract payload 상수는 `tests/fixtures/api_contract_data.py`에 배치
- 공통 payload builder (`signup/login`)는 `tests/fixtures/payload_data.py`에 배치
- 운영 유사 시드 데이터 상수는 `tests/fixtures/scenario_seed_data.py`에 배치
- 현재 공통 fixture: `sample_user` (`UserResponse`)
- fixture는 작고 조합 가능하게 유지
- 도메인 전용 fixture가 필요하면 해당 도메인 테스트 파일 인근에 정의

시드 스키마 표준 (필수):
1. 사용자 시드 스키마: `SeedUserSchema`
   - `email: str`
   - `name: str`
   - `password: str`
   - `role: str`
   - `is_verified: bool`
2. 시드 프로필 스키마: `SeedProfileSchema`
   - `profile_name: str`
   - `primary_user: SeedUserSchema`
   - `existing_user_count: int`
   - `existing_user_role: str`
   - `existing_user_email_prefix: str`
   - `existing_user_name_prefix: str`
   - `existing_user_start_index: int`
3. 기본 프로필 상수: `DEFAULT_SEED_PROFILE`
4. 시드 fixture (`seeded_integration_client`)는 임의 상수가 아닌 `SeedProfileSchema` 경로를 사용해야 함

시나리오 플로우 스키마 표준 (필수):
1. 크로스도메인 시나리오 입력 스키마는 `tests/fixtures/scenario_flow_data.py`에 배치
2. 시나리오 스키마는 다음을 선언해야 함:
   - 주체 자격증명 (로그인 이메일/비밀번호)
   - 도메인 액션 입력 (예: API 키 이름)
   - 기대 분기 플래그 (예: 비활성 키 거부)
3. 시나리오 테스트는 인라인 리터럴 대신 스키마 상수(예: `DEFAULT_FULL_SYSTEM_SCENARIO`)를 사용

## 7) Unit / Integration / E2E 정책

Unit 테스트:
1. service 또는 utility의 의사결정 로직 대상
2. repository/외부 호출은 모킹
3. 실제 DB/네트워크 없음

Integration 테스트:
1. 실제 테스트 DB/Redis 경로 사용
2. 테스트별 데이터 격리 (트랜잭션 롤백 또는 전용 reset fixture)
3. repository/query 동작이 중요한 플로우 커버
4. 기존 레코드 의존 비즈니스에는 운영 유사 시드 시나리오 포함
5. 사전 로드 상태 플로우에는 `seeded_integration_client` 사용 (기준 사용자 + 기존 사용자)
6. full-system 시나리오 플로우는 `tests/integration/scenarios/`에 유지
7. marker 경계 필수:
   - `api_test`: API 계약 테스트 전용
   - `primary_data`: 클린 프라이머리 데이터 상태의 integration 테스트
   - `mocked_data`: 운영 유사 시드 데이터 상태의 integration 테스트

E2E 테스트:
1. 실제 실행 중인 앱 인스턴스 대상으로 수행
2. 핵심 사용자 여정만 유지
3. 하위 레벨에서 이미 검증한 광범위 API 계약을 중복하지 않음

## 8) 실행 명령

백엔드 테스트 전체 실행:

```bash
cd src/backend
uv run pytest
```

API 계약 테스트만 실행:

```bash
cd src/backend
uv run pytest -m api_test
```

클린 프라이머리 데이터 통합 테스트만 실행:

```bash
cd src/backend
uv run pytest -m primary_data
```

운영 유사 시드 시나리오/통합 테스트 실행:

```bash
cd src/backend
uv run pytest -m mocked_data
```

full-system 시드 시나리오만 실행:

```bash
cd src/backend
uv run pytest -m "mocked_data and scenario_flow"
```

커밋 전 품질 체크:

```bash
cd src/backend
uv run ruff check .
uv run ruff format . --check
uv run pytest
```

## 8.1) 시드 기반 Full-System 시나리오 순서

파일:
1. `tests/integration/scenarios/test_full_system_scenario.py`

실행 마커:
1. `mocked_data`
2. `scenario_flow`

Auth 도메인 시퀀스 (`test_seeded_auth_domain_main_flow`):
1. 시드된 기준 사용자 로그인 성공
2. OAuth providers 계약 확인
3. bearer 토큰 기반 `/auth/me` 성공
4. 시드된 admin 주체 기준 `/auth/admin/user-role-stats` 성공
5. `/auth/me` 프로필 업데이트 성공
6. refresh 컨텍스트 기준 `/auth/refresh` 성공
7. `/auth/logout` 성공 및 세션 무효화
8. 로그아웃 후 `/auth/refresh` 거부 (`INVALID_TOKEN`)
9. 중복 이메일 `/auth/signup` 거부 (`EMAIL_ALREADY_EXISTS`)
10. 잘못된 비밀번호 `/auth/login` 거부 (`INVALID_CREDENTIALS`)
11. 잘못된 이메일 형식 `/auth/signup` 거부 (422)
12. `/auth/resend-verification` 계약 성공
13. `EMAIL_ENABLED` 토글 기준 `/auth/forgot-password` 분기 검증

API key 도메인 시퀀스 (`test_seeded_api_key_domain_main_flow`):
1. 시드된 기준 사용자 로그인 성공
2. `/api-keys` 생성 성공
3. 중복 키 이름 거부 (`API_KEY_NAME_ALREADY_EXISTS`)
4. `/api-keys` 목록에 생성 키 포함
5. `/auth/me`에서 API key 인증 성공
6. `/api-keys/{id}/status` 비활성화 성공
7. 비활성 키로 `/auth/me` 접근 거부 (`API_KEY_INVALID`)
8. `/api-keys/{id}/status` 활성화 성공
9. 재활성 키로 `/auth/me` 인증 성공
10. `/api-keys/{id}` 삭제 성공
11. 삭제된 키 재삭제 거부 (`API_KEY_NOT_FOUND`)

## 8.2) 테스트 데이터 라이프사이클

1. `api_test`는 DB 시드 데이터를 사용하지 않음
2. `primary_data` integration은 테스트별 격리된 임시 DB의 클린 초기 상태 사용
3. `mocked_data` integration은 테스트별 격리된 임시 DB + 시드 프로필 데이터 사용
4. 시드 데이터는 테스트 실행마다 재생성되며 임시 DB teardown 시 폐기됨

## 8.3) 에러 계약 일관성 규칙 (Static Serving 모드)

1. static serving 모드에서 SPA fallback은 비 API HTML 요청에만 적용
2. API 경로(`/api/...`) 404 응답은 예외 detail의 도메인 에러 payload shape를 유지
3. fallback 핸들러에서 API 404 detail을 plain `"Not Found"`로 덮어쓰면 안 됨

## 8.4) 현재 시나리오 인벤토리

Smoke:
1. `tests/test_smoke.py::test_ping_returns_ok`

API 계약 (`api_test`):
1. `tests/api/v1/auth/test_auth_api.py`
2. `tests/api/v1/api_key/test_api_key_api.py`
3. `tests/api/v1/events/test_events_api.py`

Integration 기본 데이터셋 (`primary_data`):
1. `tests/integration/api/v1/auth/test_auth_integration.py` primary 상태 플로우 + RBAC 금지/성공 분기
2. `tests/integration/api/v1/api_key/test_api_key_integration.py`

Integration 시드 데이터셋 (`mocked_data`):
1. `tests/integration/api/v1/auth/test_auth_integration.py` seeded 상태 플로우
2. `tests/integration/scenarios/test_full_system_scenario.py`

## 9) 네이밍 및 스타일 규칙

1. 파일명: `test_<target>.py`
2. 테스트 함수명: `test_<behavior>_<expected_result>`
3. 각 테스트 함수에는 한 줄 시나리오 docstring 필수
4. 다단계 테스트는 `Given / When / Then` 인라인 주석 사용
5. 명시적 assertion 필수 대상:
   - status code
   - 도메인 실패의 error code/message key
   - 핵심 응답 payload 필드
6. 테스트 하나는 하나의 동작에 집중

필수 형식 템플릿:

```python
def test_<behavior>_<expected_result>(...):
    """Scenario: <what flow is being verified in one sentence>."""
    # Given: <initial state or setup condition>
    # When: <action/request under test>
    # Then: <expected result/contract>
```

예시:

```python
def test_me_requires_authentication(sample_user):
    """Scenario: protected route denies access without auth dependency."""
    # Given: client without current-user override.
    # When: /api/v1/auth/me is requested.
    # Then: 401 with INVALID_TOKEN error code is returned.
```

## 10) 변경 체크리스트

백엔드 API 동작이 변경될 때:
1. `tests/api/v1/<domain>/` 아래 대응 도메인 API 테스트 업데이트
2. 부팅/핵심 라우트 계약이 바뀌었을 때만 스모크 테스트 조정
3. 영속성 의미론이 중요한 동작이면 integration 커버리지 추가
4. 문서 동기화 유지 (`BACKEND.md`, `README.md`, 필요 시 이 문서)

## 11) 신규 도메인 테스트 온보딩 규칙 (필수)

새 백엔드 도메인/라우터 추가 시 동일한 테스트 형식을 유지합니다.

필수 디렉터리 대상:
1. API 계약 테스트: `tests/api/v1/<domain>/test_<domain>_api.py`
2. Integration 테스트: `tests/integration/api/v1/<domain>/test_<domain>_integration.py`
3. 도메인이 end-to-end 비즈니스 플로우에 참여하면
   `tests/integration/scenarios/` 아래 시나리오 테스트를 추가/수정

신규 도메인 필수 최소 테스트셋:
1. API 계약 성공 케이스 (200/201)
2. API 계약 인증 실패 케이스 (보호 라우트면 401/403)
3. API 계약 요청 검증 실패 (422)
4. 빈 초기 상태에서의 integration 성공 플로우
5. 기존 레코드 의존 동작이면 시드 상태(`seeded_integration_client`) integration 시나리오 포함
6. 핵심 플로우 도메인이면 크로스도메인 시나리오 assertion 경로 추가/수정

신규 도메인 Fixture/데이터 경계 규칙:
1. 운영 유사 시드 레코드를 API 계약 데이터에 넣지 않음
2. API 계약 상수는 `tests/fixtures/api_contract_data.py`에 배치
3. 공통 요청 payload builder는 `tests/fixtures/payload_data.py`에 배치
4. 운영 유사 데이터셋 스키마/프로필은 `tests/fixtures/scenario_seed_data.py`에 배치
5. 추가 시드 시나리오가 필요하면 새 `SeedProfileSchema` 프로필을 추가하고, 임의 필드 우회 사용 금지

머지 전 리뷰 게이트:
1. docstring + Given/When/Then 형식 준수 확인
2. API vs Integration 데이터 경계 유지 확인
3. `uv run ruff check .`, `uv run ruff format . --check`, `uv run pytest` 실행
