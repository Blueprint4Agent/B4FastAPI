# Celery 백그라운드 실행

Celery 5.6 worker와 Beat를 API와 별도 프로세스로 실행합니다.
가입 인증·비밀번호 재설정 메일은 이제 Celery worker에서 실행합니다.
메일 기능을 켜면 별도 worker가 필요합니다. API 계약·DB 스키마는 유지하며
결제 작업은 추가하지 않습니다.

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
동일한 task ID로 실행 완료를 확인합니다. Beat는 생명주기 메일 outbox를 1분마다 확인합니다.
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
docker-up/deploy는 LOGIN_ENABLED와 EMAIL_ENABLED가 모두 true이면 worker를 먼저
배포하고 상태 확인 후 API를 갱신합니다. API가 fakeredis를 쓰더라도 메일 broker가
내장 Redis이면 Redis도 먼저 시작합니다. worker 상태 확인 실패 시 API 배포는
진행하지 않습니다. worker는 SMTP 설정과 선택적 시작 연결 검증을 수행합니다.
Beat는 계속 선택 사항이며 일정 변경 시 docker-celery-up으로 갱신합니다.
API와 worker의 task 계약 호환성을 유지합니다.
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
  구성합니다. 메일 작업의 제한된 재시도와 실패 보관은 아래 규칙을 따릅니다.
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

## 인증 메일 처리

AuthService는 core/mail/queue.py의 async 메서드를 호출하고 실제 SMTP 전송은
b4fastapi.mail.send task가 담당합니다. API의 BRPOP worker는 제거했습니다.
EMAIL_ENABLED=false이면 발행과 소비 모두 건너뜁니다. 기존
EMAIL_QUEUE_MAX_RETRIES=3, EMAIL_QUEUE_RETRY_DELAY_SECONDS=2를 유지하며
최초 시도 + 최대 3회 재시도입니다. countdown 대기 중 worker를 점유하지 않습니다.
EMAIL_QUEUE_BLOCK_TIMEOUT_SECONDS는 제거했으며 기존 로컬 값은 env 동기화 시
정리할 수 있습니다.

작업은 토큰 TTL에 따른 생성·만료 시각을 포함합니다. 만료되거나 잘못된 작업은
SMTP를 호출하지 않고 실패 보관합니다. 실제 토큰 검증은 API가 계속 담당합니다.
토큰 재발급·사용으로 TTL 전에 무효화된 링크까지 worker가 확인하지는 않습니다.

최종 실패는 Celery Redis의 `<CELERY_KEY_PREFIX>mail:failures` hash에 task ID를
키로 저장합니다. 원래 메시지, trace ID, 이유, 시도 횟수, 실패 시각이 포함됩니다.
같은 ID의 재저장은 덮어쓰므로 중복 기록이 쌓이지 않습니다. 로그에는 SMTP 오류
원문이나 토큰 링크를 넣지 않습니다. 실패 보관 완료도 task 완료이므로 Celery의
SUCCESS가 메일 발송 성공을 의미하지는 않습니다.

보관 실패 시 failure_reason을 포함한 새 메시지로 60초 후 보관만 재시도하며
SMTP는 다시 호출하지 않습니다. 이 보관 재시도는 Redis 복구까지 계속됩니다.
다만 새 메시지 발행 자체가 실패하거나 ACK 전에 worker가 종료되면 원래 작업이
재전달되어 SMTP가 중복 호출될 수 있습니다. 정확히 한 번 발송은 보장하지 않습니다.
worker 상태, 재시도 로그, 실패 보관 건수를 감시하고 반복 크래시는 운영자가 격리합니다.

실패 기록에는 수신자와 비밀 링크가 포함됩니다. Redis 접근을 제한하고 보관·정리
정책을 운영해야 합니다. 자동 만료나 공개 조회 API는 없으며 안전한 운영 세션에서
HLEN으로 건수, 필요할 때만 개별 기록을 확인합니다. 실패한 인증 메일은 그대로
재생하지 말고 새 링크를 요청합니다. 내구성은 Redis AOF·백업·eviction 설정에
의존합니다. SQL migration은 없습니다.

## 기존 큐에서 전환

1. 가입·인증 재발송·비밀번호 재설정 요청을 잠시 중지합니다.
2. 기존 API/worker를 유지해 queue:mail:jobs를 비우고 진행 중인 전송·재시도도
   끝났는지 확인합니다. 큐 길이 0만으로 처리 완료를 판단하지 않습니다.
3. queue:mail:dlq를 안전하게 확인·백업합니다. 이번 변경은 기존 DLQ를 지우지
   않습니다. Redis 전체를 비우거나 기존 JSON을 Celery 큐에 복사하지 않습니다.
4. 새 이미지·설정과 worker를 먼저 배포한 뒤 API를 배포합니다. Docker는 메일이
   켜져 있으면 worker 상태를 먼저 확인합니다. 수동 배포는 ping과 테스트 메일함을
   확인한 다음 요청을 재개합니다. 기존 실패 건은 새 링크 발급으로 처리합니다.
5. 롤백할 때도 발행을 중지하고 Celery 작업을 먼저 처리합니다. 구버전 API는
   Celery 메시지를 소비하지 못합니다.

자동 가져오기는 하지 않습니다. 아직 메일을 쓰지 않았거나 대기 작업이 없으면
이전할 backlog는 없습니다. 기존 producer가 발행하는 동안 새 worker만 실행하는
전환은 지원하지 않습니다.

## 이전 후 백그라운드 작업

| 대상 | 담당 | 결과 |
| --- | --- | --- |
| 가입 인증·비밀번호 재설정 메일 | Celery → MailService | 이전 완료 |
| 재시도·실패 보관 | Celery countdown·Redis hash | BRPOP·sleep·기존 list DLQ 대체 |
| worker 시작·종료 | 별도 프로세스 / Docker | API lifespan에서 제거 |
| SMTP asyncio.to_thread | Celery가 호출하는 MailService | 실행 보조로 유지 |
| SSE heartbeat·Redis 구독 | FastAPI HTTP 연결 | 유지 |
| DB migration·API SMTP 검증·readiness | API/배포 수명주기 | 유지 |

구독·계정 생명주기 메일에는 1분 간격 outbox 스캔을 사용하며 기존 인증 메일 큐는 별도로 유지합니다.
[영문 가이드](../../../src/backend/CELERY.md)에 공식 Celery 참고 링크가 있습니다.


구독 시작·플랜 변경·계정 삭제 완료 메일은 migration 0011의 암호화 outbox를 사용합니다. 삭제 완료 메일은 사용자 삭제와 같은 트랜잭션에 기록하며 단일 Celery Beat가 1분마다 복구 작업을 발행합니다. 기존 인증·환영 메일의 큐 정책은 그대로 유지합니다. 운영 설정·보존 기간·중복 전달 한계는 [결제 문서](../billing.md)를 참조하세요.

구독 정합성 작업(b4fastapi.billing.reconcile)은 300초마다 오래된 고객 상태 최대 50개를 Stripe에서 동기화합니다. 먼저 0012–0013 마이그레이션을 적용하고 Beat 하나와 Worker를 실행합니다. 프론트의 주기적 조회는 사용하지 않습니다.

생명주기 메일 조회는 SMTP 실패뿐 아니라 종료된 워커 임대도 포함해 5회로 제한합니다. 수신 정보 없는 CLI 복구와 72시간 수신 정보 삭제 정책은 [생명주기 메일 운영](../lifecycle-mail.md)을 따릅니다.
