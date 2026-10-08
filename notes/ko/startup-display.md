# 시작 및 종료 화면

API의 기본값은 `STARTUP_DISPLAY=auto`입니다. 폭 76칸 이상의 대화형 터미널에는
청록색 B4A 배너, 서비스 아이콘, 영어 상태 표가 표시됩니다. 서비스 역할,
설정된 스택, 활성화 여부, 실제 점검 결과를 각각 분리합니다.
상단에는 APP_MODE 기준 `Mode: Development/Production`과 LOGIN_ENABLED 기준
`Login: Enabled/Disabled`를 표시합니다. 로그인을 끈 개발 환경에는
`Bootstrap session`을 덧붙입니다. APP_ENV는 실행 모드가 아닌 관측용 라벨입니다.

스택은 설정에서 판별합니다: Local/Amazon S3/Cloudflare R2/Supabase,
Google/GitHub, Gmail SMTP(그 외 호스트는 SMTP), Stripe Test/Live,
PostgreSQL/SQLite. 스택 이름 자체는 연결 성공을 뜻하지 않습니다.

- `Yes / Checking…`: 활성화되어 점검 중입니다.
- `Yes / Verified`: 해당 서비스의 시작 검증이 완료되었습니다.
- `Yes / Configured`: 설정 검증만 완료되었습니다. OAuth에 사용하며, SMTP 연결
  점검을 껐다면 `Connection check skipped`를 함께 표시합니다.
- `No / Not checked`: 비활성화되어 점검하지 않았습니다.
- `Failed`: 점검 실패로 시작을 중단합니다. 뒤의 활성 서비스는 `Not run`입니다.
- Database는 `Migrating… → Initializing… → Ready`로 진행합니다.

정상 종료 시 같은 스타일의 표에서 Database, Cache, Storage가
`Closing… → Closed`로 바뀝니다. Cache는 Redis 또는 Redis · In-memory이며,
지연 생성 클라이언트를 열지 않았다면 `Not opened`입니다. API 프로세스의
클라이언트 정리이며 외부 DB·Redis 서버나 Celery worker를 종료하는 것은 아닙니다.
DB 정리에 실패해도 Redis와 스토리지 정리는 시도합니다. 모든 정리가 성공한
정상 종료에만 마지막으로 `B4A · Bye!!`를 표시합니다. 시작 실패, 정리 실패,
강제 프로세스 종료에서는 정상 종료 인사를 표시하지 않습니다.

| 설정 | 동작 |
| --- | --- |
| `STARTUP_DISPLAY=auto` | 터미널 애니메이션, Docker·파일 출력에서는 정적인 배너와 결과 표 |
| `STARTUP_DISPLAY=plain` | 줄 단위 시작·종료 상태 로그 |
| `STARTUP_DISPLAY=off` | 기존 서비스·Uvicorn 시작·종료 로그 |
| `NO_COLOR=1` | 색상 제거, 터미널 갱신은 유지 |
| `LOG_LEVEL=WARNING` 이상 | INFO 수준 화면과 종료 인사 미출력 |

Docker·파일 출력에는 커서 애니메이션 없이 배너와 최종 시작·종료 표를 남깁니다.
로그 수집용 줄 단위 출력은 plain을 선택합니다. 좁거나 기능이 제한된 터미널, `--workers`, `WEB_CONCURRENCY`,
`UVICORN_WORKERS`로 확인되는 다중 worker에서는 일반 로그를 사용합니다.
Python 코드로 다중 worker를 지정한다면 `STARTUP_DISPLAY=plain`을 설정합니다.
reload 관리 프로세스의 로그는 유지되며, 교체되는 앱 프로세스마다 점검합니다.

중복 로그는 콘솔에서만 정리합니다. 원본 로그는 OTLP·파일 핸들러에서 유지하고,
경고·오류는 표 위에 표시합니다. 연결 문자열·비밀번호·공급자 응답은 표에
추가하지 않습니다. Cache는 OAuth·메일·결제·DB 초기화 전에 5초 제한으로 Redis PING을 수행합니다.
실패하면 시작을 중단하고 확보한 클라이언트를 정리합니다. Redis · In-memory는
개발용 FakeRedis입니다. 시작 때 연 클라이언트는 종료 표에서 정리합니다.
실제 worker 검증이 없는 Celery를 정상으로 표시하지 않습니다.

원문: [Startup and shutdown display](../startup-display.md).

## 요청 로그

콘솔 요청 로그는 로컬 `HH:MM:SS`, 정렬된 메서드·경로, 상태 코드 순서로 표시합니다.
클라이언트 임시 포트, 반복되는 INFO 접두어, HTTP 버전은 콘솔에서 생략합니다.
전체 경로와 쿼리 문자열은 자르지 않습니다. 성공한 2xx OPTIONS 사전 요청만
콘솔에서 숨기며, 실패한 OPTIONS와 실제 요청은 유지합니다. 파일·OTLP 핸들러에는
클라이언트·프로토콜·성공 OPTIONS를 포함한 원본 Uvicorn 기록이 전달됩니다.
기존 정확한 /metrics 경로 제외 정책과 CORS·실제 요청 처리는 변경하지 않습니다.

일반 서버·앱 메시지도 같은 시간·레벨 열을 사용합니다. INFO/WARNING/DEBUG/ERROR/
CRITICAL을 정렬하고 DEBUG·오류에는 [출처]를 표시합니다. LOG_LEVEL=DEBUG에서는
다른 레벨도 출처·상관관계 정보를 유지합니다. 기존 request/trace/task ID 정책과
예외 스택 트레이스를 보존하며, 실제 출력 스트림과 NO_COLOR에 맞춰 색상을 적용합니다.
사용자가 지정한 파일 포맷터와 수집기로 전달하는 원본 기록은 변경하지 않습니다.

터미널 메서드 색상은 GET 초록, POST 청록, PUT 노랑, PATCH 보라, DELETE 빨강,
HEAD 파랑, OPTIONS 회색입니다. 시간은 회색, API 경로는 밝은 파랑이며 상태 코드는
HTTP 상태별 색상을 유지합니다. 색상 적용 전에 열 너비를 맞춰 색상 유무에 따라
정렬이 달라지지 않습니다. Docker·파일 출력은 명시적인 터미널·색상 강제 설정이
없는 한 ANSI 제어문자를 포함하지 않습니다.
