# 결제 흐름 점검 — 이슈 #93

점검일: 2026-10-08. 기준: 작업 시작 전 상위 main, 고정 B4React `d4878ea`.
현재 Stripe 연동을 점검했으며 새 결제 제공자를 추가하지 않았습니다.

## 재현한 문제와 수정

| 문제 | 재현·영향 | 수정 |
| --- | --- | --- |
| 업그레이드 후 구독 ID 누락 | Plus→Pro 응답의 플랜은 저장되지만 DB `stripe_subscription_id`가 null로 바뀝니다. Stripe 구독 자체가 삭제되는 것은 아닙니다. | 결제 대기를 포함해 `updated.id`를 상태와 함께 저장합니다. |
| 복수 구독에서 기존 구독 없음 표시 | 같은 고객의 활성 구독 두 개를 반환하면 unknown 상태지만 `has_subscription=false`였습니다. UI는 신규 구매를 허용할 수 있었으나 서버는 차단했습니다. | `has_subscription=true`와 변경 불가 상태를 저장합니다. 기존 저장값은 다음 동기화 시 복구됩니다. |
| Checkout 내부 객체 모드 검사 누락 | 정상 외부 세션 안의 SetupIntent·Subscription이 모드 불일치/누락이어도 성공으로 판정했습니다. 실제 Stripe 사고가 아닌 합성 회귀 테스트입니다. | 세션과 내부 객체의 모드를 모두 확인한 뒤 registered/paid를 반환합니다. |
| 오래된 문서 설명 | 앞부분의 웹훅 미구현 설명이 뒤의 DB·Beat 구현 설명과 충돌했습니다. | 한국어·영어 결제 문서와 백엔드 가이드를 정리했습니다. |

수정 전 추가한 검증에서 6건이 실패했고 수정 후 통과했습니다.
API 스키마·마이그레이션·제공자 쓰기·프런트 소스 변경은 없습니다.

## 재현 가능한 흐름별 점검표

백엔드 테스트 경로는 `src/backend/tests/` 기준입니다.

| 흐름 | 근거와 확인 결과 |
| --- | --- |
| 카드·Link 등록 | `unit/services/test_billing.py`, `test_billing_sdk.py`, `integration/api/v1/billing/test_native_management.py`: 서버 등록 확인, 소유권·모드, 재시도 키, 실제 SDK 직렬화. Link에 카드 정보를 임의로 넣지 않습니다. |
| 기본 결제수단·삭제·청구 정보 | `test_native_management.py`: 소유자 범위, 활성 기본 수단 삭제 금지, 주소 구조. 프런트는 각 영역 오류를 독립적으로 복구합니다. |
| 신규 구독·취소 복귀 | `test_subscription_integration.py`: 서버 가격, 소유권·모드·결제 완료 검증, bearer/API 키, 동시 예약 및 같은 재시도 파라미터. URL만으로 결제를 인정하지 않습니다. |
| 업그레이드·다운그레이드·해지·복원 | `test_plan_management.py`: Plus→Pro 결제 대기 중 기존 등급 유지. 다운그레이드·주기 변경·해지는 기간 종료 시 적용하고 복원은 해지 예약을 해제합니다. 오래된 버전·외부 일정은 거부합니다. |
| 장애·웹훅 중복·역순 | 서명된 이벤트를 받고 현재 Stripe 상태를 다시 조회합니다. 장애 시 502와 기존 DB 상태를 유지하며 같은 이벤트 재전송 후 복구합니다. |
| 웹훅 누락 | Beat 재조정 테스트에서 외부 상태 변경 후 DB를 복구합니다. 일반 조회는 DB를 읽으므로 동기화 후 새로고침해야 합니다. |
| 청구서 | `test_native_management.py`: 페이지 커서·상세의 소유권/모드와 추가 항목 여부. 브라우저 테스트는 내역·상세를 앱 모달로 확인합니다. |
| 통화·가격 | 모드·통화·반복 주기가 틀린 가격은 고객/Checkout 생성 전에 거부합니다. 금액은 통화 최소 단위이며 구독 변경은 기존 통화를 유지합니다. |
| UI 재진입·복구 | 훅·컴포넌트·API 31개, 브라우저 결제 시나리오 52개 통과. 모바일/데스크톱·한국어·복귀 URL·취소·결제 대기·인증 복구를 포함합니다. 계정별 공유 상태와 명시적 새로고침을 사용하며 브라우저 포커스 폴링은 없습니다. |
| 메일 이벤트 중복 | DB와 서명 이벤트로 시작/플랜 변경을 중복 수신해 각각 한 건만 예약하며 오래된 플랜 이벤트는 예약하지 않습니다. 기존 테스트는 비활성·갱신/실패 메일 제외도 검증합니다. |

저장소 루트에서 재실행합니다.

```sh
make backend-test PYTEST_ARGS='tests/integration/api/v1/billing tests/unit/services/test_billing.py tests/unit/services/test_billing_sdk.py tests/unit/services/test_billing_startup.py tests/unit/mail/test_lifecycle_notifications.py'
make -C src/frontend test-selected TEST_FILES='src/tests/integration/hooks/billing src/tests/integration/api/billingApi.test.ts src/tests/component/components/features/billing'
make -C src/frontend test-ui-selected TEST_FILES=tests/e2e/billing.spec.ts
make verify-plan
make verify
```

집중 백엔드 검증은 91개 통과했습니다. 전체 선택 검증 결과는
[작업 기록](../../worklog/0221-billing-flow-audit.md)에 있습니다.
브라우저 테스트는 결제 API를 모킹하고 DB 통합 테스트는 Stripe 응답을 대체합니다.
실제 Stripe 결제창이나 외부 전달 성공을 증명하는 검증은 아닙니다.

## 실제 테스트 환경 읽기 전용 검증

테스트 키 환경에서 `BillingService.initialize()`와 `plans()`가 통과했습니다.
Checkout 읽기·가격·제한된 포털 설정 정책을 확인했고 고객·세션·결제·환불·메일은 생성하지 않았습니다.
반환된 가격 8개는 다음과 같습니다.

| 등급·주기 | KRW 최소 단위 | USD 최소 단위 |
| --- | ---: | ---: |
| Plus 월간 | 3990 | 399 |
| Plus 연간 | 43092 | 4309 |
| Pro 월간 | 11970 | 1197 |
| Pro 연간 | 129276 | 12928 |

로컬 웹훅 비밀키는 **미설정**입니다. 외부 서명 이벤트 수신, Stripe 카드/Link/3DS 화면,
Worker·Beat 배포, Dashboard 메일 스위치는 **확인하지 않았습니다**.
운영 전 결제 가이드의 snapshot 이벤트 목록·서명 키를 설정하고 Worker와 Beat 하나를 실행한 뒤,
통제된 수신자로 테스트 모드 Checkout·결제 실패를 확인해야 합니다.
이 배포 확인은 #93에 남기며 이 PR로 운영 활성화 완료를 주장하지 않습니다.

## #95에 넘길 확정 이벤트·메일 경계

| 이벤트 | 확정 조건 | 앱 메일 | 제공자 담당 |
| --- | --- | --- | --- |
| 최초 `invoice.paid` | subscription_create, paid 청구서, 현재 active·고객/모드 일치·알려진 가격 | 계정 사용자 이메일로 구독 시작 | 금전 영수증 |
| `customer.subscription.updated` | 실제 가격 변경, active, 결제 대기 없음, 현재 가격이 이벤트와 일치 | 계정 사용자 이메일로 적용 완료 | 금전 영수증 |
| `customer.subscription.deleted` | 요청에 따른 해지 완료, 새 비종료 구독 없음 | 계정 사용자 이메일로 Free 전환 완료 | Stripe 해지 안내를 설정했다면 앱 완료 안내와 중복하지 않도록 조정 |
| 갱신 `invoice.paid` | 현재 상태 동기화 | 없음 | 갱신 영수증·선택한 사전 알림 |
| `invoice.payment_failed` / `payment_action_required` | 현재 상태 동기화, 업그레이드 권한 부여 금지 | 없음 | 실패·복구·인증 메일과 조치 링크 |
| 해지 예약·복원 | 제공자 변경 확인, 해지 완료와 구분 | 없음 | 선택한 제공자 안내와 중복 방지 |

Stripe는 영수증·복구 알림, 앱은 계정/플랜 상태 안내를 담당합니다.
이는 책임 구분이며 Dashboard 기본 발송이 켜져 있다는 뜻은 아닙니다.
운영 전 Customer emails와 Billing 복구 설정을 확인하고 #95에서 영수증·실패 알림을 중복 추가하지 않습니다.
공식 [영수증 설정](https://docs.stripe.com/receipts),
[고객 메일 설정](https://docs.stripe.com/billing/revenue-recovery/customer-emails)을 참고하세요.

Stripe는 [이벤트 순서를 보장하지 않습니다](https://docs.stripe.com/webhooks#event-ordering).
현재 핸들러는 제공자 상태를 다시 읽으며 메일은 의미 기반 키로 중복 제거합니다.
#95에서는 같은 초에 반복되는 동일 가격 전환의 키 충돌, 나중 플랜 변경 뒤 늦게 온 최초 청구서,
해지 완료 전달, 언어 보존(`b4a_language` 미지정 시 현재 영어), 운영 재시도 권한과 보존 정책을 점검해야 합니다.
이는 이번에 수정한 결제 상태와 별개인 알림 범위입니다. 브로커·SMTP 장애가 완료된 도메인 변경을
되돌리면 안 되며 기존 outbox 제약은 결제 가이드를 따릅니다. 이번에는 메일 발송·계정 삭제 범위를 추가하지 않았습니다.

## 운영 제약

Stripe 변경과 로컬 DB 커밋은 하나의 원자적 트랜잭션이 아닙니다.
응답이 불확실하면 기존 요청 UUID로 재시도하고 새로고침·재조정해야 합니다.
페이지 재진입으로 키를 잃거나 제공자 멱등 기간이 만료된 경우, 일정 해제/수정 일부만 성공한 경우에는
운영자 확인이 필요할 수 있습니다. Dashboard 직접 변경은 앱 변경과 조율해야 합니다.
등급 표시는 사용량/권한 체계가 아닙니다. 향후 기능은 unknown·past_due를 유료 권한의 근거로 사용하면 안 됩니다.
