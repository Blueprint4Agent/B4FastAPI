# Billing audit — issue #93

Audit date: 2026-10-08. Baseline: parent main before this task; pinned B4React
`d4878ea`. Scope is the existing Stripe integration, not a new provider.

## Reproduced defects and corrections

| Finding | Reproduction and impact | Correction |
| --- | --- | --- |
| Upgrade loses subscription identity | Upgrade Plus to Pro; API returns the new plan but DB `stripe_subscription_id` becomes null. Provider subscription is not deleted. | Save `updated.id` with the snapshot, including pending-payment responses. |
| Multiple subscriptions advertise no subscription | Return two active subscriptions for one customer; persisted `unknown` had `has_subscription=false`. UI could offer another purchase, although server rejects it. | Persist `has_subscription=true`, unknown/non-manageable state. Existing snapshots are repaired by the next sync. |
| Expanded object mode unchecked | Complete, owner-matched Checkout with an expanded SetupIntent/Subscription whose mode differs or is absent still reports success. This is a synthetic defensive regression, not evidence Stripe returned inconsistent objects. | Verify the inner object mode as well as the session before returning registered/paid. |
| Stale guide describes absent webhooks | Earlier billing sections contradicted the later DB snapshot/Beat implementation. | Reconcile English/Korean guides and backend guide. |

The added assertions failed before service changes (six failures), then passed.
No API schema, migration, provider writes or frontend source changes are required.

## Reproducible flow checklist

Backend test paths below are relative to `src/backend/tests/`.

| Flow | Evidence and expected result |
| --- | --- |
| Card / Link registration | `unit/services/test_billing.py`, `test_billing_sdk.py`, `integration/api/v1/billing/test_native_management.py`: server-confirmed setup, owner/mode checks, idempotent setup, real SDK transport serialization; Link does not invent card metadata. |
| Default / removal / profile | `test_native_management.py`: owner-scoped writes, active default cannot be removed, structured address; frontend section failures recover independently. |
| New subscription / cancel return | `test_subscription_integration.py`: server-owned prices, owner/mode/paid checks, bearer/API-key access, concurrent reservations and identical retry parameters. Return query alone never proves payment. |
| Upgrade / downgrade / cancel / restore | `test_plan_management.py`: Plus→Pro uses pending payment; old tier remains pending. Downgrade/interval/cancel apply at period end; restore clears cancellation. Stale versions and unsupported schedules fail closed. |
| Provider outage / duplicate / out-of-order webhook | Signed integration events fetch current provider state, never apply an old event snapshot. Failure returns 502, preserves DB state, and the same redelivered event repairs it. |
| Missing webhook | Beat reconciliation test repairs a stored subscription after provider change. Requests read DB; external changes require synchronization before reload. |
| Invoice history | `test_native_management.py`: pagination cursor/detail owner/mode isolation and line pagination indication. Browser test keeps history/detail in a modal. |
| Currency / catalog | Invalid mode/currency/recurrence is rejected before customer/Checkout creation. Prices use minor units; subscription changes retain the existing currency. |
| UI state / re-entry / recovery | Existing billing hook/component/API tests: 31 passed. Browser billing scenarios: 52 passed, including mobile/desktop, KR labels, redirect checks, cancellation, payment pending and credential recovery. Shared snapshot is account-scoped, with explicit reload and no browser focus polling. |
| Lifecycle event deduplication | New DB-backed signed-event test reserves one start and one applied plan-change notification despite duplicates; obsolete plan event reserves none. Existing mail tests cover disabled mode and ignored renewal/failure. |

Commands (from repository root):

```sh
make backend-test PYTEST_ARGS='tests/integration/api/v1/billing tests/unit/services/test_billing.py tests/unit/services/test_billing_sdk.py tests/unit/services/test_billing_startup.py tests/unit/mail/test_lifecycle_notifications.py'
make -C src/frontend test-selected TEST_FILES='src/tests/integration/hooks/billing src/tests/integration/api/billingApi.test.ts src/tests/component/components/features/billing'
make -C src/frontend test-ui-selected TEST_FILES=tests/e2e/billing.spec.ts
make verify-plan
make verify
```

Focused backend: 91 passed. Full selected verification results are in
[worklog](../worklog/0221-billing-flow-audit.md). Browser tests mock the billing API;
DB integration tests stub Stripe. They do not prove hosted Stripe UI or live delivery.

## Read-only sandbox evidence

The configured test-key environment passed `BillingService.initialize()` and `plans()`:
Checkout read access, enabled catalog and restricted portal policy validated without
creating customers, sessions, payments, refunds or emails. Eight prices were returned:

| Tier / interval | KRW minor units | USD minor units |
| --- | ---: | ---: |
| Plus monthly | 3990 | 399 |
| Plus annual | 43092 | 4309 |
| Pro monthly | 11970 | 1197 |
| Pro annual | 129276 | 12928 |

The local webhook secret is **unset**. External signed delivery, hosted card/Link/3DS,
worker/Beat deployment and Dashboard mail switches are **not verified** by this audit.
Before production, register the snapshot webhook event list in the billing guide,
configure its signing secret, run one Beat and a worker, and exercise test-mode
Checkout and payment failure with controlled recipients. This deployment checklist
remains tracked under #93; no production activation is claimed by this PR.

## Confirmed event / email boundary for #95

| Event | Confirmed condition | Application mail | Provider responsibility |
| --- | --- | --- | --- |
| Initial `invoice.paid` | subscription_create, paid invoice, current active subscription with matching customer/mode and recognized price | Subscription started; account user's email | Monetary receipt |
| `customer.subscription.updated` | Actual price transition, active, no pending update, current provider price matches event | Applied plan change; account user's email | Any financial receipt |
| `customer.subscription.deleted` | Canceled by request, no newer nonterminal subscription | Completion / Free transition; account user's email | Configured Stripe cancellation notice must not duplicate app completion notice |
| Renewal `invoice.paid` | Current provider sync | None | Renewal receipt and optional advance reminder |
| `invoice.payment_failed` / `payment_action_required` | Current provider sync; never grant an upgrade | None | Failure/recovery/authentication email and hosted action |
| Cancellation scheduled / restored | Provider-confirmed mutation; not an ended subscription | None | Optional provider notices; avoid duplicate lifecycle messages |

Use Stripe for receipts and recovery reminders; app messages describe account/plan
state only. These are responsibilities, not proof Dashboard defaults are enabled.
Inspect Dashboard Customer emails and Billing revenue-recovery settings before launch;
do not enable a second application receipt or failure reminder in #95. Stripe documents
[receipt configuration](https://docs.stripe.com/receipts) and
[customer email controls](https://docs.stripe.com/billing/revenue-recovery/customer-emails).

Stripe [does not guarantee event order](https://docs.stripe.com/webhooks#event-ordering).
The current handler re-fetches provider state; notification keys are semantic. Follow-up
#95 must review same-second repeated transitions (current key includes timestamp/price pair),
late initial invoices after later plan changes, cancellation delivery, locale persistence
(`b4a_language` currently falls back to English), operator retry access and retention.
These are notification-scope gaps, not fixed by this billing-state audit. Broker/SMTP
failure must not reverse a completed domain change; current outbox limitations remain
in the billing guide. No notification delivery or account deletion scope is added here.

## Operational limitations

Provider side effects and a local DB commit are not one atomic transaction. An ambiguous
management response can require reload/reconciliation; retry the same request UUID while
it remains available. After reload/idempotency expiry or partial schedule release/update,
operator reconciliation can be necessary. Remote Dashboard writes must be coordinated.
Local tier display is not a quota/authorization system. Unknown or past-due states must
not be treated as proof of a paid feature entitlement by future features.
