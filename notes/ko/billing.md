# Stripe·Link 카드 등록 기본 구성

[English](../billing.md)

이번 단계는 청구 없이 결제수단을 등록하는 기반입니다. Stripe Checkout의 `setup`
모드에서 `card`, `link`를 제공합니다. 카드 입력·인증·보관은 Stripe가 담당하고,
서버에는 고객 ID, 생성 식별자, 테스트/실서비스 구분, 생성 시각만 저장합니다.
카드 번호·CVC·client secret을 앱에서 받거나 보관하지 않습니다. Link는 Stripe 지갑입니다.

## 설정과 테스트

1. `make backend-install`, `make env-sync`를 실행합니다. 배포 환경은
   `make docker-env-sync`를 사용합니다. 비밀 키는 백엔드/배포 `.env`에만 넣습니다.
2. `STRIPE_ENABLED=true`, `STRIPE_SECRET_KEY=sk_test_...`를 설정합니다.
   `STRIPE_SETUP_SUCCESS_URL`, `STRIPE_SETUP_CANCEL_URL`은 운영자가 정한 절대 HTTP(S)
   URL입니다. 성공 URL에는 `{CHECKOUT_SESSION_ID}`가 반드시 있어야 합니다.
   요청에서 URL을 받지 않으며 실서비스 키 사용 시 HTTPS가 필수입니다.
3. 해당 Stripe 샌드박스/계정 Dashboard에서 Link를 활성화합니다. 실제 제공 여부는
   계정 자격과 설정에 따릅니다. 앱 DB 하나에 Stripe 계정 하나를 사용하세요.
   계정을 바꾸려면 기존 고객 매핑을 점검해야 합니다. 테스트/실서비스 매핑은 분리합니다.
4. 서버 시작 시 Alembic이 0007 다음 `0008_billing_customers`를 적용합니다.
   운영 DB는 정상 배포 절차에 따라 백업합니다. 롤백은 로컬 매핑만 삭제하며 Stripe
   객체는 그대로입니다. 결제 기능이 꺼져 있어도 앱은 시작됩니다.
5. `/docs`의 Authorize에서 OAuth2PasswordBearer를 선택하고 앱 이메일을 username,
   앱 비밀번호를 password로 입력합니다. `/api/v1/auth/token`으로 bearer 토큰을
   발급받습니다. 또는 APIKeyHeader에 앱 API 키를 입력해 X-API-Key로 인증합니다.
   Stripe 비밀 키는 서버 전용 설정이며 사용자 API 인증용이 아닙니다.
   이후 결제 설정을 조회합니다.
   `POST /api/v1/billing/setup-sessions`에 다음과 같이 UUID를 전달합니다.

   ```json
   {"request_id":"9a3f996f-7e30-4be4-8d74-86f4d8366b29"}
   ```

6. 응답 `url`을 열어 Stripe 테스트 카드 `4242 4242 4242 4242`, 미래 만료일,
   임의의 세 자리 CVC로 등록하거나 가상 사용자 정보로 Link를 테스트합니다.
   샌드박스 Link에는 실제 카드나 개인정보를 넣지 않습니다.
7. 복귀 후 인증된 `GET /api/v1/billing/setup-sessions/{session_id}`를 호출합니다.
   Checkout 완료와 본인 SetupIntent 성공을 모두 확인해야 `registered=true`입니다.
   복귀 URL, 취소, 만료, 진행 중 상태만으로 완료 처리하지 않습니다.
8. `GET /api/v1/billing/payment-methods?method_type=card`와 `method_type=link`를
   각각 조회합니다. `has_more=true`이면 `next_cursor`를 `starting_after`로 전달합니다.
   `limit`은 1–100, 기본 20입니다. 카드는 브랜드·끝 네 자리·만료일만 반환하며
   Link에는 카드 필드가 없을 수 있습니다.

기본 복귀 URL은 설정의 결제 화면을 열고 상태 API로 등록 완료를 검증합니다.
프로필 메뉴에서 사이드바 없는 독립 전체 화면으로 Free·월간·연간 플랜을 선택하고 우측 상단에서 닫을 수 있습니다. 월간 ₩3,990 / US$3.99,
연간 ₩39,900 / US$39.99는 샌드박스 예시이며 서버에 설정한 Stripe Price에서 조회합니다. 환율 환산이 아닙니다.
카드·Link 등록과 구독 Checkout을 연결하며 거래 내역과 취소 UI는 아직 제공하지 않습니다.
[프론트 결제 가이드](../../src/frontend/notes/ko/billing.md)를 참고하세요.
Stripe 제공 화면을 사용하므로 프론트엔드 공개 키나 Stripe.js는 필요하지 않습니다.

## 동작과 제한

Billing API 8개 모두 bearer 세션 또는 앱 API 키(`X-API-Key`)로 접근합니다.
기존 키도 재발급 없이 소유자 권한으로 사용할 수 있습니다. 두 인증을 함께 보내면
둘 다 유효하고 같은 사용자여야 합니다. Swagger에서 키만 테스트할 때는 만료된
OAuth2 인증을 Logout한 뒤 APIKeyHeader만 등록하세요.
`GET /api/v1/billing/config`는 `enabled`, `livemode`만 공개합니다.
비활성은 `BILLING_DISABLED`(503)이며, 활성화된 설정이 미완료면 이제 서버 시작을
중단합니다. 실행 중 Stripe 장애/시간 초과는
`BILLING_UNAVAILABLE`(502), 본인 소유가 아닌 세션이나 없는 세션은
`BILLING_NOT_FOUND`(404)입니다. 성공 응답은 `no-store`이며 추가 입력 필드를 거부합니다.

동일 등록 요청의 재시도에는 같은 UUID를 사용하고 새 등록에는 새 UUID를 만듭니다.
Stripe 멱등성은 영구적인 중복 방지 보장이 아닙니다. 사용자/모드별 원자적 예약으로
고객 생성 식별자를 고정합니다. 아직 고객 ID가 연결되지 않은 예약이 23시간 이상이면
Stripe의 24시간 이후 키 정리 가능성 때문에 `BILLING_RECONCILIATION_REQUIRED`(409)로
중단합니다. 운영자는 Stripe의 `billing_identity`/`user_id` 메타데이터를 확인해 기존
고객을 연결하거나, 원격 생성이 없었다고 확인한 후에만 예약을 다시 만듭니다.
실패했다고 식별자를 무조건 바꾸면 중복 고객이 생길 수 있습니다.
SDK 요청 제한은 5초, 네트워크 재시도 1회, 서비스 외부 호출 전체 제한은 20초입니다.

Stripe가 등록 상태의 원본이며 조회는 고객을 생성하지 않습니다. 웹훅, 로컬 결제 상태,
기본 결제수단 지정, 삭제/연결 해제, 청구서 UI, 이용권, 알림은 아직 구현하지 않았습니다. 구독 Checkout과 직접 조회 방식은 아래 설명을 따릅니다.
결제에 따른 로컬 상태 변경을 추가할 때 서명 검증·중복 처리 방지를 갖춘 웹훅이 필요합니다.
현재 요청/응답 기반 구성에는 워커·실시간 이벤트 루프가 해당하지 않습니다.
후속 UI는 복귀·계정 전환·연결 복구 시 재조회하고 URL 파라미터를 완료 근거로 삼지 않습니다.

로컬 계정 삭제 시 고객 매핑은 삭제되지만 **Stripe 고객이나 저장 결제수단은 삭제되지
않습니다.** 원격 보관 정책과 자동 정리/재시도 설계는 운영 도입 전에 필요합니다.
모의 테스트 통과는 실제 Stripe 계정 연결이나 카드 등록 완료를 의미하지 않습니다.

## 공식 자료

- [Checkout 결제수단 저장](https://docs.stripe.com/payments/checkout/save-and-reuse)
- [Checkout의 Link 설정](https://docs.stripe.com/payments/link/checkout-link)
- [Stripe Python SDK](https://github.com/stripe/stripe-python)
- [Stripe 테스트 카드](https://docs.stripe.com/testing)

## 서버 시작 시 Stripe 검증

SMTP 초기화처럼 DB 마이그레이션과 요청 수신 전에 Stripe 검증을 완료합니다.
`STRIPE_ENABLED=false`면 비활성 로그만 남기며 설정 검증이나 외부 통신을 하지 않습니다.
`true`일 때는 다음을 순서대로 수행합니다.

1. 비밀/제한 키 형식, 두 복귀 URL과 포트, 성공 URL 플레이스홀더, 실서비스 HTTPS를
   확인합니다. 오류에는 잘못된 환경변수 이름만 표시하고 입력 값은 노출하지 않습니다.
2. 실제 비동기 SDK로 `GET /v1/checkout/sessions?limit=1`을 호출합니다. 새 샌드박스의
   빈 목록도 성공입니다. 고객·등록 세션·결제를 생성하지 않고 조회 데이터는 기록하지 않습니다.
3. 성공 후에만 `Stripe startup verification succeeded (mode=test/live)`를 남깁니다.
   인증 실패, Checkout 읽기 권한 부족, 네트워크/API 장애, 시간 초과는 서버 시작을
   중단하며 원본 응답이나 비밀 키를 포함하지 않는 사유를 표시합니다. HTTP 클라이언트는
   성공/실패 모두 정리합니다.

기존 요청 제한 5초, SDK 네트워크 재시도 1회, 외부 호출 전체 제한 20초를 재사용합니다.
활성화 상태에서 검증을 건너뛰는 별도 설정은 없습니다. API 워커마다 시작할 때 검사하며
상시 상태 확인이나 Celery 작업은 아닙니다. 따라서 Stripe 장애 시 활성화된 신규 API
프로세스는 시작할 수 없습니다.
이 검사는 인증·연결과 Checkout **읽기 권한**을 확인하며, 구독 활성화 시 4개 Price도 읽고 검증합니다. 쓰기 권한, Link 제공/활성화,
실계정 활성화, 복귀 URL 접속 가능 여부, 실제 카드 등록 성공까지 보장하지는 않습니다.
샌드박스 등록 흐름도 별도로 테스트하세요.
[공식 조회 API](https://docs.stripe.com/api/checkout/sessions/list) 참고.

## 요청·응답 예시

실제 스키마에 맞춘 설명용 예시이며 ID와 URL은 실행 가능한 Stripe 객체가 아닙니다. 아래 등록 API들은 다음 헤더로 호출합니다.

```http
X-API-Key: <APPLICATION_API_KEY>
```

1. `GET /api/v1/billing/config` → **200**

```json
{"enabled": true, "livemode": false}
```

2. `POST /api/v1/billing/setup-sessions` → **201**

Request:
```json
{"request_id": "9a3f996f-7e30-4be4-8d74-86f4d8366b29"}
```

Response:
```json
{"id": "cs_test_example", "url": "https://checkout.stripe.com/c/pay/example"}
```

3. `GET /api/v1/billing/setup-sessions/cs_test_example` → **200**

```json
{"id": "cs_test_example", "status": "complete", "registered": true}
```

4. `GET /api/v1/billing/payment-methods?method_type=card&limit=20` → **200**

```json
{
  "items": [{"id": "pm_example", "type": "card", "brand": "visa", "last4": "4242", "exp_month": 12, "exp_year": 2030}],
  "has_more": false,
  "next_cursor": null
}
```

`GET /api/v1/billing/payment-methods?method_type=link` → **200**

```json
{
  "items": [{"id": "pm_linkexample", "type": "link", "brand": null, "last4": null, "exp_month": null, "exp_year": null}],
  "has_more": false,
  "next_cursor": null
}
```

Empty:
```json
{"items": [], "has_more": false, "next_cursor": null}
```

Invalid API key → **401**:
```json
{"detail": {"error": "API_KEY_INVALID", "message": "Invalid API key."}}
```

반환된 URL을 브라우저에서 열어 등록을 완료합니다. 같은 작업의 재시도에만 request_id를 재사용합니다. 미완료/만료 상태는 status가 open/expired이고 registered=false입니다. status만 보지 말고 registered를 확인하세요. has_more=true이면 next_cursor를 starting_after로 전달합니다. 비활성화 시 config는 enabled=false이며 나머지는 503 BILLING_DISABLED입니다. 기타 오류는 403 API_KEY_USER_MISMATCH, 404 BILLING_NOT_FOUND, 409 BILLING_RECONCILIATION_REQUIRED, 422 입력 검증, 502 BILLING_UNAVAILABLE입니다.

플랜 카드 영역 우측 상단의 작은 드롭다운으로 통화를 선택합니다. 플랜 선택 화면의 결제수단 등록 영역은 제거했으며 카드·Link 등록은 설정의 결제 화면에서 제공합니다.

결제 섹션은 기존 설정의 헤더·본문 간격과 행 카드 스타일을 재사용하며, 프론트 브라우저 검증에서 일반 설정과 실제 배치를 비교합니다.

## 구독 Checkout

`STRIPE_SUBSCRIPTIONS_ENABLED`를 켜기 전에 월간·연간/원화·달러의 4개 Price ID를 설정합니다.
환경 변수는 `STRIPE_MONTHLY_KRW_PRICE_ID`, `STRIPE_MONTHLY_USD_PRICE_ID`,
`STRIPE_ANNUAL_KRW_PRICE_ID`, `STRIPE_ANNUAL_USD_PRICE_ID`입니다. 활성·양수·per-unit·licensed
정기 가격이어야 하며 통화, 월/년 주기와 키의 테스트/실서비스 모드가 일치해야 합니다.
서버 시작 시 읽기 전용으로 검증하며 가격을 자동 생성하지 않습니다. 모드별 ID를 분리합니다.

`STRIPE_CHECKOUT_SUCCESS_URL`은 프론트의 `/settings?billing_checkout={CHECKOUT_SESSION_ID}`,
취소 URL은 `/settings?billing_checkout=cancelled`로 설정합니다. 실서비스는 HTTPS가 필수이며
환경 변경 후 백엔드를 재시작합니다. Docker 환경은 로컬 설정과 별개입니다.

- `GET /api/v1/billing/plans`: `{enabled, livemode, prices: [{plan, currency, amount}]}`를 반환합니다.
  금액은 최소 통화 단위이며 비활성 구독은 빈 가격 목록입니다.
- `GET /api/v1/billing/subscription`: Stripe의 현재 `{plan, status, currency,
  current_period_end, cancel_at_period_end, has_subscription}`을 반환합니다. 구독이 없으면
  free/none, 모르는 가격은 unknown이며 복수 구독이나 불완전한 목록은 운영자 확인 오류입니다.
- `POST /api/v1/billing/checkout-sessions`: `{request_id, plan: monthly|annual,
  currency: krw|usd}`를 받아 `{id,url}`을 반환합니다. 고객·가격·금액·복귀 주소는 서버 소유입니다.
- `GET /api/v1/billing/checkout-sessions/{session_id}`: `{id,status,paid}`를 반환합니다.
  같은 고객·사용자·모드의 complete/paid 세션과 active 구독을 확인해야 `paid=true`입니다.

마이그레이션 0009는 사용자/모드별 가격·UUID·1시간 만료의 예약을 저장합니다. 기기나 요청 UUID가
달라도 같은 Stripe 멱등 키와 인자로 재시도합니다. 다른 가격, 기존 미종료 구독, 만료까지
31분 미만인 예약은 `BILLING_CHECKOUT_CONFLICT`(409)입니다. 마지막 조건은 불명확한 재시도에서
Stripe의 최소 만료 제한 때문에 인자를 바꾸지 않기 위한 것입니다. 기존 결제를 완료하거나
최초 1시간이 만료된 뒤 재시도합니다. 만료 후 새 예약을 잡고 구독을 다시 확인합니다.
앱 외부에서 같은 고객의 세션을 추가 생성해 예약을 우회하지 마세요.

구독 상태는 요청 시 Stripe에서 직접 조회합니다. 로컬 유료 이용권·웹훅 투영·백그라운드 동기화는
없으며 결제에 따른 로컬 부수 효과를 도입하기 전에 서명·중복 검증이 필요합니다. 기존 구독의
변경·취소는 운영자가 Stripe에서 처리하며 UI는 추가 구독 구매를 막습니다.

Checkout 예약 이력이 있는 계정 삭제는 운영자 확인 오류 `ACCOUNT_BILLING_REVIEW_REQUIRED`(409)로
막습니다. 사용자 행을 잠근 뒤 확인하여 예약 외래 키와 삭제가 경쟁해 구독이 남지 않게 합니다.
삭제를 위해 예약 이력을 정리하기 전 테스트/실서비스 고객 모두에서 열린 세션을 만료시키고,
정기 구독이 취소됐으며 생성 중인 요청이 없는지 확인해야 합니다. 자동 Stripe 취소 기능은 아닙니다.
