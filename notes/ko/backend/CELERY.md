# Celery 백그라운드 실행

Celery 5.6 worker와 Beat를 API와 별도 프로세스로 실행합니다.
이번 구성은 기반 추가와 기존 작업 조사입니다. 메일 전송 경로, API 계약,
DB 스키마는 바뀌지 않으며 결제 작업도 추가하지 않습니다.

## 로컬 실행

`make backend-install`, `make env-sync` 후 실제 Redis를 실행합니다.
`src/backend/.env`의 `CELERY_BROKER_URL`이 비어 있으면 기존 Redis 연결 설정을
사용합니다. API의 `REDIS_IN_MEMORY=true`와 관계없이 Celery는 실제 Redis가
필요합니다. TLS 연결은 `rediss://` URL을 사용하고 비밀키를 명령행에 넣지 않습니다.

각 터미널에서 실행합니다.

```sh
make celery-worker
make celery-beat
make celery-ping
make celery-probe
```

probe 출력 ID는 발행 확인입니다. worker 로그의 `Celery probe completed`와
동일한 task ID로 실행 완료를 확인합니다. Beat의 업무 스케줄은 비어 있습니다.
배포당 Beat 하나만 실행합니다. 로컬 기본 풀은 macOS용 solo이고 프로세스 기반
시간 제한을 보장하지 않습니다. Linux 운영은 prefork를 사용합니다.
`CELERY_POOL=prefork CELERY_CONCURRENCY=2 make celery-worker`로 실행할 수 있습니다.
로컬 Beat 파일은 `CELERY_BEAT_SCHEDULE`로 지정하며 기본값은
`/tmp/b4fastapi-celerybeat`입니다. 여러 배포는 경로를 구분합니다.

## Docker

`make docker-build`, `make docker-env-sync` 후 `docker/.env`에 실제 broker를
설정합니다. 내장 Redis는 `cd docker && docker compose up -d redis`로 먼저
실행하고 외부 Redis를 쓰면 해당 URL을 설정합니다. 루트에서 실행합니다.

```sh
make docker-celery-up
make docker-celery-down
```

선택형 celery 프로필은 앱 이미지로 worker(prefork 2개)와 Beat를 실행하고
Beat 상태를 볼륨에 저장합니다. 이 명령은 DB/Redis를 자동으로 교체하지 않습니다.
기존 docker-up/deploy는 API만 갱신하므로 이미지 배포 후 docker-celery-up도
실행해야 합니다. API와 worker의 task 계약 호환성을 유지합니다.
컨테이너 간 Redis 주소에 localhost를 쓰지 않습니다. 시작 재시도는 있지만
Compose 시작 성공이 worker 준비 완료를 뜻하지는 않습니다. worker 컨테이너에서
`./.venv/bin/celery -A app.core.celery.app:celery_app inspect ping` 및
`call b4fastapi.probe`로 확인합니다. API readiness는 Celery 상태를 검사하지 않습니다.

## 실행 규칙

- JSON, UTC, 설정 가능한 전용 큐와 Redis 키 접두사를 사용합니다. Redis를
  공유하는 배포마다 CELERY_QUEUE와 CELERY_KEY_PREFIX를 다르게 지정합니다.
  접두사는 접근 권한 격리를 대신하지 않습니다.
- 완료 후 ACK, worker 유실 시 재전달, prefetch 1, soft/hard 제한 240/300초,
  visibility timeout 3600초입니다. 중복 실행이 가능하므로 작업 멱등성이 필요합니다.
  반복적으로 프로세스를 종료시키는 작업은 계속 재전달될 수 있어 감시·격리가 필요합니다.
- 일반 예외의 자동 재시도는 없습니다. 도메인별 일시 오류에 한정해 재시도를
  구성합니다. 현재 메일 DLQ에 해당하는 Celery 실패 저장소는 아직 없습니다.
- async publish_task는 스레드에서 발행하고 task/trace ID를 전달합니다.
  인자 로그 표시를 숨겨도 broker에는 실제 payload가 저장됩니다. 발행 오류는
  호출 서비스로 전달하며 타임아웃은 결과 불명일 수 있습니다. task ID만으로
  중복 실행이 방지되지는 않습니다.
- 로그 상관관계만 연결하며 OTel span은 전달하지 않습니다. 별도 프로세스에서
  기존 API의 OTel exporter 초기화는 실행되지 않습니다.
- 결과 backend는 비활성입니다. 구독 일정·멱등키는 향후 DB에 저장하고 Beat는
  짧은 실행 대상 조회 작업을 발행합니다. 한 달 countdown은 사용하지 않습니다.
  DB와 broker 간 유실 방지가 필요하면 outbox와 복구 절차를 추가합니다.
  Redis의 AOF·백업·eviction 정책도 내구성에 영향을 줍니다.
- Celery는 결제나 SMTP의 정확히 한 번 실행을 보장하지 않습니다.

## 기존 백그라운드 작업 조사

| 대상 | 판단 | 이전 시 필요한 작업 |
| --- | --- | --- |
| task_queue/services/mail.py의 가입 인증·비밀번호 재설정 메일 | Celery 이전 우선 후보, 현재 유지 | EMAIL_ENABLED, async 발행 인터페이스, SMTP 검증, 언어, 로그, 재시도·실패 보관 유지 |
| task_queue/worker.py의 BRPOP·재시도 sleep·DLQ | 메일 이전 시 대체 | 기존 queue:mail:jobs 비우기 및 queue:mail:dlq 확인, 중복 전송·만료 링크 정책 마련 |
| bootstrap.py/main.py의 메일 worker 시작·종료 | 메일 이전 시 제거 | 새 worker를 먼저 배포하고 발행 경로 전환, 기존 메시지는 Celery와 형식이 다름 |
| SMTP asyncio.to_thread | 스케줄러가 아닌 실행 보조 | Celery task 안에서 재사용 가능 |
| SSE heartbeat·Redis 구독 루프 | API에 유지 | HTTP 연결·취소 수명주기에 종속 |
| 시작 시 DB migration·SMTP 검증·readiness | 기존 수명주기에 유지 | 시작 완료와 서비스 준비 여부의 전제 조건 |

추가적인 애플리케이션 create_task/FastAPI BackgroundTasks 작업이나 기존 정기
결제·정리 스케줄러는 발견하지 못했습니다. 메일 실제 이전은 별도 후속 변경입니다.

[영문 가이드](../../../src/backend/CELERY.md)의 공식 Celery 참고 링크도 확인하세요.
