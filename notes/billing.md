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
4. Start the API normally; startup Alembic applies `0008_billing_customers` after migration 0007. Back up production databases before normal rollout. Downgrade drops the local
   mapping table only; it cannot undo remote Stripe objects. The app still boots with billing disabled.
5. In Swagger `/docs`, open Authorize and use OAuth2PasswordBearer with your app
   email as username and your app password. This obtains a bearer token through
   `/api/v1/auth/token`. Alternatively, enter your application API key in APIKeyHeader (X-API-Key).
   The Stripe secret key is server-only and does not authenticate these routes. Read billing config,
   then `POST /api/v1/billing/setup-sessions` with a UUID body:

    ```json
    { "request_id": "9a3f996f-7e30-4be4-8d74-86f4d8366b29" }
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

The default return URLs open the Billing section in Settings and verify registration
through the status API. The profile menu opens standalone Free/Plus/Pro selection.
Subscription prices now come from configured Stripe Price IDs; sandbox examples are monthly
₩3,990 / US$3.99 and annual ₩43,092 / US$43.09 for Plus. They are not FX conversions. Card/Link
registration, subscription Checkout, invoices and period-end plan management are connected. See the [frontend billing guide](../src/frontend/notes/billing.md). Hosted Checkout
needs no frontend publishable key or Stripe.js dependency.

## Contract and failure behavior

All sixteen operations accept a bearer session or an application API key (`X-API-Key`).
Keys act as their owner; existing keys gain billing access without reissuance.
When both credentials are sent, both must be valid and identify the same user.
In Swagger, clear expired OAuth2 authorization before testing only an API key.
`GET /config` under `/api/v1/billing` exposes `enabled`, `livemode` and optional `publishable_key`; secret keys remain server-only.
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
No webhook endpoint, local payment projection or entitlement enforcement is implemented. Default payment method and invoice summaries are read from Stripe; profile/card editing uses its restricted portal. Subscription Checkout and read-through status are described below. Add verified,
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
The probe verifies authentication/connectivity and Checkout **read** permission; with subscriptions enabled it also reads and validates the four Price objects.
It does not prove write permissions, Link eligibility/enabling, live account activation,
return URL reachability or successful card registration; complete the sandbox flow too.
Read API reference: [List Checkout Sessions](https://docs.stripe.com/api/checkout/sessions/list).

## Request and response examples

Illustrative schema-correct payloads; IDs and URLs are not usable provider objects. The registration calls below can use this header.

```http
X-API-Key: <APPLICATION_API_KEY>
```

1. `GET /api/v1/billing/config` → **200**

```json
{ "enabled": true, "livemode": false }
```

2. `POST /api/v1/billing/setup-sessions` → **201**

Request:

```json
{ "request_id": "9a3f996f-7e30-4be4-8d74-86f4d8366b29" }
```

Response:

```json
{ "id": "cs_test_example", "url": "https://checkout.stripe.com/c/pay/example" }
```

3. `GET /api/v1/billing/setup-sessions/cs_test_example` → **200**

```json
{ "id": "cs_test_example", "status": "complete", "registered": true }
```

4. `GET /api/v1/billing/payment-methods?method_type=card&limit=20` → **200**

```json
{
    "items": [
        {
            "id": "pm_example",
            "type": "card",
            "brand": "visa",
            "last4": "4242",
            "exp_month": 12,
            "exp_year": 2030
        }
    ],
    "has_more": false,
    "next_cursor": null
}
```

`GET /api/v1/billing/payment-methods?method_type=link` → **200**

```json
{
    "items": [
        {
            "id": "pm_linkexample",
            "type": "link",
            "brand": null,
            "last4": null,
            "exp_month": null,
            "exp_year": null
        }
    ],
    "has_more": false,
    "next_cursor": null
}
```

Empty:

```json
{ "items": [], "has_more": false, "next_cursor": null }
```

Invalid API key → **401**:

```json
{ "detail": { "error": "API_KEY_INVALID", "message": "Invalid API key." } }
```

Open the returned URL to finish hosted registration. Reuse request_id only for retries of the same action. Status may also be open or expired, with registered=false; trust registered, not status alone. With has_more=true, pass next_cursor as starting_after. Disabled billing returns config enabled=false, while provider calls return 503 BILLING_DISABLED. Other failures: 403 API_KEY_USER_MISMATCH, 404 BILLING_NOT_FOUND, 409 BILLING_RECONCILIATION_REQUIRED, 422 validation, 502 BILLING_UNAVAILABLE.

The plans screen uses a compact currency dropdown above the cards at the upper right. Card/Link registration is available only in Settings Billing; plan selection has no registration action.

Billing reuses the existing settings header/content spacing and row surfaces; frontend browser checks compare its geometry with General settings.

## Subscription Checkout

Enable `STRIPE_SUBSCRIPTIONS_ENABLED` only after setting all four recurring Price IDs:
`STRIPE_MONTHLY_KRW_PRICE_ID`, `STRIPE_MONTHLY_USD_PRICE_ID`,
`STRIPE_ANNUAL_KRW_PRICE_ID`, `STRIPE_ANNUAL_USD_PRICE_ID`. Prices must be active,
positive per-unit licensed recurring prices, matching the configured month/year and
currency and the key's test/live mode. Startup validates them read-only. No provider
resources are auto-created at server startup. Use separate test/live IDs.

Set `STRIPE_CHECKOUT_SUCCESS_URL` to the frontend's
`/settings?billing_checkout={CHECKOUT_SESSION_ID}` and cancel to
`/settings?billing_checkout=cancelled`. Live mode requires HTTPS. Restart the backend
after environment changes. Docker has its own environment; local settings do not enable it.

- `GET /api/v1/billing/plans`: `{enabled, livemode, prices: [{plan, currency, amount}]}`;
  amount is minor currency units. Disabled subscriptions return an empty catalog.
- `GET /api/v1/billing/subscription`: current Stripe `{plan, status, currency,
current_period_end, cancel_at_period_end, has_subscription}`. No subscription means
  `plan=free,status=none`; unfamiliar prices mean `plan=unknown`, never Free. Multiple
  subscriptions or an incomplete list require operator reconciliation.
- `POST /api/v1/billing/checkout-sessions`: `{request_id, plan: monthly|annual,
currency: krw|usd}` → `{id,url}`. Customer, price, amount and return URL are server-owned.
- `GET /api/v1/billing/checkout-sessions/{session_id}`: `{id,status,paid}`. `paid=true`
  requires a complete, paid Checkout and active subscription belonging to the same
  customer/user/mode. A URL parameter or complete/unpaid session does not prove payment.

Migration 0009 stores a customer/mode Checkout reservation with a fixed price, UUID and
one-hour expiration. Different devices/UUIDs converge on the same provider idempotency
key and parameters. A different price, an existing nonterminal subscription, or an
attempt with less than 31 minutes left returns `BILLING_CHECKOUT_CONFLICT` (409). The
last case avoids changing Stripe's minimum expiration constraint during ambiguous retries;
finish the existing hosted session or wait until the original hour expires. After expiry,
reserve a new attempt and recheck subscriptions before creating. Do not bypass reservations
by creating additional sessions for the same customer outside this application.

The backend reads Stripe subscription state directly on request; it does not implement
local paid entitlements, webhook projections or background synchronization. Add signed,
replay-safe event handling before payment-driven local side effects. Supported subscriptions can be changed/cancelled at period end through the authenticated management endpoint; unsupported/externally managed states require operator review. The UI prevents a second purchase.

Accounts with any Checkout reservation history cannot be deleted until operator review
(`ACCOUNT_BILLING_REVIEW_REQUIRED`, 409). The user row is locked before checking history,
so deletion cannot race the reservation foreign key and orphan a subscription. Before
clearing that owner's reservation for deletion, inspect both test/live customer records,
expire open sessions, and confirm all recurring subscriptions are cancelled with no pending
creation. This is deliberately operator reconciliation, not automatic Stripe cancellation.

## Period-end management and billing details

`POST /billing/subscription/change` accepts `{plan: free|monthly|annual|keep, expected_version, request_id}`. Read `change_version` from the current subscription immediately before confirmation. An account/mode database lock serializes changes across workers; stale or unsupported changes return `BILLING_CHANGE_CONFLICT` (409). Existing subscriptions keep their currency. `pending_plan` and `pending_effective_at` describe the reservation while `plan` remains the current plan.

Free sets cancel_at_period_end; keep clears cancellation or releases this application's schedule. Monthly/annual changes use two Stripe schedule phases and no prorations; renewal starts the new billing interval. No immediate refunds or charges occur. Only simple active single-item subscriptions without discounts, trials, tax-rate overrides, transfers, pauses or external schedules support self-service. A provider failure between schedule creation and ownership marking may require operator reconciliation; refresh and review state before retrying. Direct Dashboard mutations must be coordinated with application changes.

`GET /billing/profile` returns customer email/name/address, effective default payment-method ID and portal availability. `GET /billing/invoices` returns the four most recent invoices in minor currency units; View all opens Stripe. `POST /billing/portal-sessions` takes request UUID and overview/customer_update/payment_method_update flow. The server owns the customer and return URL. Set STRIPE_PORTAL_CONFIGURATION_ID to an active configuration with customer_update (email/name/address), payment_method_update and invoice_history enabled, but subscription_cancel/update disabled; runtime rejects configurations that bypass app plan policy. Leave it blank to disable portal actions. The local sandbox configuration is provisioned in ignored backend .env; production and Docker remain separately configured.

All sixteen endpoints accept bearer/application API keys with no-store responses. Required Stripe permissions additionally include customer/invoice reads, subscription/schedule writes, and portal session creation/configuration reads. No card numbers are handled by this application. Scheduled execution belongs to Stripe; local paid entitlements still require a separate webhook design.

When STRIPE_PORTAL_CONFIGURATION_ID is set, startup performs a read-only active/mode/feature-policy validation. Runtime repeats this check before creating each portal session.

## In-app profile and card management

Set optional `STRIPE_PUBLISHABLE_KEY` (`pk_test_…` or `pk_live_…`) for embedded card entry; its mode must match the secret key. Local and Docker `.env.example` files include the blank setting; actual account values belong in the environment. Config exposes only this public key, enablement and mode. An unset public key leaves read/profile/default/removal APIs usable and disables embedded registration.

- `PUT /billing/profile`: `{request_id,email,name,address:{country,city,state,line1,line2,postal_code}}`; returns the provider profile including `address_fields` and display `address`.
- `POST /billing/payment-methods/{method_id}`: `{request_id,action:default|remove}`; owner/mode checks and customer lock precede provider writes. Default updates both customer and the single active subscription. Removing its active default returns `409 BILLING_METHOD_REQUIRED`; select a replacement first.
- `POST /billing/card-setups`: `{request_id}`; creates an off-session card-only SetupIntent for the authenticated customer and returns `{id,client_secret}` with no-store. The secret is for Stripe Elements only; never log or persist it.
- `GET /billing/card-setups/{intent_id}`: `{registered}`; true requires succeeded SetupIntent, attached payment method and matching customer/user/mode. Return URLs alone never prove registration.

Setup/default/detach writes require corresponding Stripe permissions. Raw card numbers and CVC go directly from Elements to Stripe. Link methods identify a wallet; their API object does not expose underlying card brand/last four/expiry. Only real card methods provide these fields. Invoice overview remains in the restricted portal. No webhook entitlement projection is added.

## Tiers and billing intervals

Free, Plus and Pro are product tiers. Each paid pricing card owns an independent
monthly/annual SegmentedControl; currency remains a shared preview control.
The server-owned purchase keys `monthly`/`annual` represent Plus and
`pro_monthly`/`pro_annual` represent Pro. These preserve existing clients and
subscriptions while separating tier labels from billing intervals in the UI.

| Tier | Monthly KRW / USD | Annual KRW / USD |
| ---- | ----------------- | ---------------- |
| Plus | 3,990 / 3.99      | 43,092 / 43.09   |
| Pro  | 11,970 / 11.97    | 129,276 / 129.28 |

These are the configured sandbox examples, not hardcoded checkout amounts. Annual
billing is approximately 10% less than twelve monthly payments (USD rounds to cents).
The cards show a monthly equivalent, annual total and provider-derived discount.
`STRIPE_PLUS_{MONTHLY|ANNUAL}_{KRW|USD}_PRICE_ID` optionally overrides the legacy Plus
purchase prices. Keep legacy `STRIPE_{MONTHLY|ANNUAL}_{KRW|USD}_PRICE_ID` values so
existing subscriptions remain recognized and retain their price. Pro uses optional
`STRIPE_PRO_{MONTHLY|ANNUAL}_{KRW|USD}_PRICE_ID` values; unavailable options cannot be
purchased. Every configured price is checked for mode, currency and recurring interval.
No existing subscription is migrated by changing the catalog.

Plus → Pro applies immediately only after Stripe accepts payment, using
`payment_behavior=pending_if_incomplete` and `proration_behavior=always_invoice`.
Changing the interval during an upgrade can start a new billing cycle. A pending
payment retains the old plan, blocks further mutations and exposes an owner/mode-checked
hosted invoice link for payment/authentication. This explicit recovery action opens
Stripe; it is not the deferred in-app invoice-history modal. Focus/online recovery
reads the provider again; no client-side entitlement is granted. Pro → Plus, same-tier
interval changes and cancellation apply at period end, preserving paid time.
See [Stripe pending updates](https://docs.stripe.com/billing/subscriptions/pending-updates).

The route shell owns the sidebar subscription snapshot through the existing
hook and passes its tier through layout props. It resets on account changes and never maps roles or URL selections to a paid tier.
A successful mutation invalidates other mounted subscription consumers; each rereads
the server. Unknown/error states do not display a misleading Free badge. The collapsed
avatar shows an accessible compact tier mark; the expanded profile menu shows the
full name above email with stronger weight and tier text treatment. No new state store,
webhook, feature quota or tier-specific application entitlement is introduced here.
