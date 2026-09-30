# Stripe and Link registration foundation

Korean: [카드 등록 기본 구성](ko/billing.md).

This phase saves a payment method without creating a charge or subscription. The app
creates a Stripe-hosted Checkout Session in `setup` mode with `card` and `link`.
Stripe handles card entry, authentication and storage. The backend stores only a
customer ID, random creation identity, mode and timestamp. No PAN/CVC/client secret
is accepted by the app. Link is a Stripe wallet, not a separate card vault operated here.

## Configure and test

1. Run `make backend-install` and `make env-sync` (deployment: `make docker-env-sync`).
   Set values in the backend or deployment `.env`; never put the secret key in Vite.
2. Set `STRIPE_ENABLED=true`, `STRIPE_SECRET_KEY=sk_test_...`, and trusted absolute
   `STRIPE_SETUP_SUCCESS_URL` / `STRIPE_SETUP_CANCEL_URL`. Success must include the
   literal `{CHECKOUT_SESSION_ID}` placeholder. Both URLs are controlled by the operator,
   never accepted from a request. Live keys require HTTPS return URLs.
3. Enable Link for the intended Stripe sandbox/account in Dashboard payment-method settings.
   Stripe availability depends on account eligibility and configuration. Use one Stripe
   account per application database; switching accounts requires mapping reconciliation.
   Test/live mappings are isolated; do not repoint existing mappings to a different account.
4. Start the API normally; startup Alembic applies `0008_billing_customers` after migration
   0007. Back up production databases before normal rollout. Downgrade drops the local
   mapping table only; it cannot undo remote Stripe objects. The app still boots with billing disabled.
5. In Swagger `/docs`, open Authorize and use OAuth2PasswordBearer with your app
   email as username and your app password. This obtains a bearer token through
   `/api/v1/auth/token`. Neither X-API-Key nor the Stripe secret key authenticates
   billing routes. Read billing config,
   then `POST /api/v1/billing/setup-sessions` with a UUID body:

   ```json
   {"request_id":"9a3f996f-7e30-4be4-8d74-86f4d8366b29"}
   ```

6. Open the returned `url`. In Stripe test mode, register test card `4242 4242 4242 4242`
   with a future expiry and any three-digit CVC, or test Link using synthetic account data.
   Do not use real card/personal information in sandbox Link accounts.
7. After returning, call `GET /api/v1/billing/setup-sessions/{session_id}` with the
   authenticated session. Only `registered=true` proves both completed Checkout and a
   succeeded SetupIntent owned by this user. Cancel/open/expired sessions are not success.
8. Query `GET /api/v1/billing/payment-methods?method_type=card` and separately `method_type=link`.
   Follow `next_cursor` as `starting_after` while `has_more=true`; `limit` is 1–100 (20 default).
   Card summaries include brand/last4/expiry; Link summaries may have no card fields.

The default return URLs open existing Settings. **This phase adds no billing Settings
screen or automatic return-URL handler**; use Swagger to confirm registration. The typed
B4React `useBillingApi` adapter is ready for a subsequent page. Stripe-hosted Checkout
needs no frontend publishable key or Stripe.js dependency.

## Contract and failure behavior

All four operations require a bearer session; API-key-only requests are rejected.
`GET /config` under `/api/v1/billing` exposes only `enabled` and `livemode`.
Disabled configuration gives `BILLING_DISABLED` (503) on provider operations;
enabled but incomplete configuration now aborts startup before serving requests;
provider failures/timeouts become sanitized `BILLING_UNAVAILABLE` (502). A foreign or
missing setup session gives `BILLING_NOT_FOUND` (404). Success responses use `no-store`.
Customer IDs are server-owned and never supplied by callers. Extra setup fields are rejected.

Reuse one request UUID for retries of the same setup action, and create a new UUID for a
new registration. Stripe idempotency is bounded, not a permanent exactly-once guarantee.
An atomic per-user/mode reservation fixes customer creation parameters across concurrency
and ambiguous network failures. If an unbound reservation is at least 23 hours old, creation
fails with `BILLING_RECONCILIATION_REQUIRED` (409) before Stripe's 24-hour pruning window.
The operator must inspect Stripe customer metadata `billing_identity`/`user_id`, reconcile
and bind the existing customer ID, or establish that no customer was created before
recreating the reservation. Do not blindly rotate a reservation after an ambiguous failure.
SDK requests use 5-second timeouts, one network retry, and a 20-second service provider budget.

Stripe remains authoritative; reads do not create customers or write registration state.
No webhook endpoint, local payment projection, default payment method, deletion/detachment,
charge, invoice, subscription, entitlement or notification is implemented. Add verified,
replay-safe webhook processing before introducing any payment-driven local side effect.
No worker/realtime loop is needed for this request/response-only foundation. A future UI
must refetch on return and account/connectivity recovery and must not trust query parameters.

Local user deletion cascades local customer mappings but **does not delete Stripe customers
or detach saved methods**. Operators own remote data retention/reconciliation; automated
remote cleanup and its durable retry workflow must be designed before production launch.
No live Stripe account or end-to-end provider registration is verified by mocked tests.

## References

- [Stripe: save payment details with Checkout](https://docs.stripe.com/payments/checkout/save-and-reuse)
- [Stripe: Link with Checkout](https://docs.stripe.com/payments/link/checkout-link)
- [Stripe Python SDK](https://github.com/stripe/stripe-python)
- [Stripe test cards](https://docs.stripe.com/testing)

## Stripe startup verification

Like SMTP initialization, the API lifespan awaits Stripe initialization before database
migrations and before serving traffic. With `STRIPE_ENABLED=false`, it logs that Stripe
is disabled and does no validation or network access. With `STRIPE_ENABLED=true`, it:

1. Validates the secret/restricted key prefix, both return URLs (including ports), the
   success placeholder, and HTTPS in live mode. Errors name fields but never their values.
2. Uses the installed async SDK to issue a read-only `GET /v1/checkout/sessions?limit=1`.
   Successful empty lists are valid, including a fresh sandbox. No customer, session or
   payment is created; the returned session data is discarded and never logged by this probe.
3. Logs `Stripe startup verification succeeded (mode=test/live)` only after success.
   Invalid authentication, denied Checkout read permission, network/API failures or timeout
   abort startup with a sanitized reason. The HTTP client is closed on success and failure.

The existing limits apply: 5-second requests, one SDK network retry and a 20-second
provider budget. There is no separate bypass flag when Stripe is enabled. Each API worker
performs its own check on start; this is not continuous readiness polling or a Celery task.
A Stripe outage therefore prevents a new Stripe-enabled API process from becoming ready.
The probe verifies authentication/connectivity and Checkout **read** permission only.
It does not prove write permissions, Link eligibility/enabling, live account activation,
return URL reachability or successful card registration; complete the sandbox flow too.
Read API reference: [List Checkout Sessions](https://docs.stripe.com/api/checkout/sessions/list).
