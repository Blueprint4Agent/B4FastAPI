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
   발급받습니다. X-API-Key나 Stripe 비밀 키로는 결제 API 인증이 되지 않습니다.
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

기본 복귀 URL은 기존 Settings를 엽니다. **이번 단계에는 앱 내부 결제 설정 화면이나
복귀 URL 자동 처리 기능이 없습니다.** Swagger에서 등록을 확인하세요. B4React의
`useBillingApi` 타입/API 연결부는 후속 화면에서 사용할 수 있도록 준비합니다.
Stripe 제공 화면을 사용하므로 프론트엔드 공개 키나 Stripe.js는 필요하지 않습니다.

## 동작과 제한

모든 API는 bearer 세션이 필요하며 API 키만으로 접근할 수 없습니다.
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
기본 결제수단 지정, 삭제/연결 해제, 청구, 구독, 이용권, 알림은 아직 구현하지 않았습니다.
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
이 검사는 인증·연결과 Checkout **읽기 권한**을 확인합니다. 쓰기 권한, Link 제공/활성화,
실계정 활성화, 복귀 URL 접속 가능 여부, 실제 카드 등록 성공까지 보장하지는 않습니다.
샌드박스 등록 흐름도 별도로 테스트하세요.
[공식 조회 API](https://docs.stripe.com/api/checkout/sessions/list) 참고.
