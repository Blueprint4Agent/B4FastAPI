# Additional payment providers — issue #94

[한국어](ko/payment-provider-research.md). Researched **2026-10-08** against official
sources and parent `f608b46` / B4React `d4878ea`. Related: [#93 audit](billing-audit-93.md),
[#95 mail policy](lifecycle-mail.md). This is a research decision, not provider activation.

## Decision and requirements

**Keep the current Stripe implementation; defer adding a second provider.** The template
has a tested billing lifecycle, but seller eligibility, target market and settlement
requirements have not been supplied. A generic adapter now would hide real differences
in subscription scheduling, checkout UI and tax responsibility. This is an engineering
conclusion from the comparison below, not a claim that Stripe is suitable for every merchant.

| Dimension | Confirmed template behavior | Decision still required |
| --- | --- | --- |
| Product | Plus/Pro monthly/annual subscriptions | Actual product and allowed business category |
| Countries | Korean/English UI | Seller legal country, buyer countries; **확인 필요** |
| Currency | KRW/USD price catalog, integer minor units | Charge/settlement currency and FX policy |
| Methods | Card/Link setup, provider-hosted checkout | Domestic wallets, bank transfer, domestic recurring coverage |
| Billing | Immediate paid tier upgrade; period-end downgrade/cancel | Trials, usage billing, one-time purchases, grace period |
| Receipts/tax | Stripe receipts, separate app lifecycle mail | Seller tax/receipt obligations, MoR preference; **확인 필요** |
| Refund/dispute | Provider dashboard; no app refund endpoint | Partial refunds, dispute owner, refund accounting/access |
| Settlement | Not modeled locally | Bank country/currency, payout timing, reserves and thresholds |
| Economics | Sandbox Plus USD 3.99/month | Volume, ticket size, refund/dispute rate and commercial quote |

Select candidates by domestic-method coverage, complete subscription behavior, seller
onboarding, operational responsibility, testability, and total cost—not payment API shape
alone. Toss Payments represents a direct domestic PG, PortOne a multi-PG integration
layer, and Paddle a software-focused Merchant of Record (MoR). These are different roles.

## Official comparison

| Option | Capability / onboarding / test evidence | Cost evidence and limits |
| --- | --- | --- |
| Current Stripe Payments + Billing | Existing card/Link, Checkout, schedules, portal and signed webhooks. Seller eligibility must be checked against [availability](https://stripe.com/global). This integration is not Stripe Managed Payments/MoR. | Public [pricing](https://stripe.com/pricing) showed 2.9% + USD 0.30 domestic-card example and Billing pay-as-you-go 0.7% of Billing volume. Country-specific rates, FX, tax products and disputes prevent treating this as our merchant quote. |
| Toss Payments direct | [Billing guide](https://docs.tosspayments.com/guides/v2/billing) supports card and bank-transfer automatic billing, subject to risk review/additional contract; the merchant implements its subscription cycle. Use the [hosted billing UI](https://docs.tosspayments.com/guides/v2/billing/integration), not raw card collection. Test keys/sandbox precede live activation. | [Public fee table](https://www.tosspayments.com/about/fee): general card 3.4%, VAT extra; listed signup KRW 220,000 and annual management KRW 110,000 depend on contract. Automatic-billing quote, settlement, eligible methods and preferential rates need confirmation. General one-time wallet support is not recurring-wallet support. |
| PortOne V2 + contracted PG | [KCP example](https://developers.portone.io/opi/ko/integration/pg/v2/kcp-v2) exposes billing-key issuance and scheduled payments. Each PG/channel determines actual methods and prerequisites; this is not automatically a full Stripe Subscription equivalent. [V2 API](https://developers.portone.io/api/rest-v2/overview?v=v2) documents idempotency and provider latency. Test a selected PG channel, not an abstract aggregate. | [Platform pricing](https://www.portone.io/pricing): Free below KRW 50m monthly net transactions; displayed monthly Growth tiers KRW 100k/300k/500k. [PG processing fees](https://help.portone.io/category/pricing) are a separate comparison dimension; confirm the combined contract/usage quote. Free platform usage does not mean free card processing. |
| Paddle Billing | [MoR](https://www.paddle.com/paddle-101) option for software, handling customer payment/tax operations. [Verification](https://developer.paddle.com/api-reference/verifications/) includes domain/business/identity checks; acceptance is not assumed. [Separate sandbox](https://developer.paddle.com/sdks/sandbox/) supports isolated credentials/data. | [Pricing](https://www.paddle.com/pricing): 5% + USD 0.50 per Checkout transaction; bespoke low-ticket pricing can be requested. Do not compare only percentage rates or assume merchant acceptance. |

Paddle lists [KRW and USD payment currencies](https://developer.paddle.com/concepts/sell/supported-currencies/),
but payout currencies differ; KRW pricing is not proof of KRW settlement or Korean seller
approval. Its [payout guide](https://www.paddle.com/help/manage/get-paid/when-and-how-do-i-get-paid)
describes monthly payouts and a minimum USD 100 threshold; country/bank charges need review.
For Toss/PortOne, obtain the actual merchant/PG settlement contract rather than promising
a generic payout day. Refund/dispute handling must be tested in each provider's sandbox
and responsibility assigned before adoption; no live refund is part of this research.

Illustrative arithmetic, not a quote: at USD 3.99, Paddle's listed fixed+percentage fee
is USD 0.6995 (about 17.53%) before rounding/any case-specific adjustments. Low ticket size
therefore matters. The current Stripe example would be about USD 0.44364 (11.12%) with
both the displayed domestic-card fee and 0.7% Billing fee, before other costs. The two
commercial offers have different included services and cannot establish a winner by
these numbers alone. No comparable KRW quote is inferred by converting currencies.

## Existing code coupling

| Area | Observed dependency | Required boundary if adopted |
| --- | --- | --- |
| `app/services/billing.py` | Direct Stripe SDK, recurring Price allowlist, SetupIntent, Checkout, Subscription/Schedule, portal, hosted invoice URLs | Provider adapter behind service orchestration; provider-specific capabilities and error normalization |
| `app/models/billing.py` | Customer primary key `(user_id, livemode)`, stripe customer/subscription IDs; same owner/mode Checkout reservation | Provider/account/environment identity and namespace-aware unique keys; preserve existing Stripe rows |
| `app/routers/v1/billing.py` | cs_/pm_/in_ path validation and current provider response shape | Versioned provider-neutral public references or provider-routed endpoints; regenerate backend/child contracts together |
| `billing_notifications.py` / reconciliation | Stripe signatures, event names, current-state reads and Stripe-enabled scans | Isolated verification adapters → normalized confirmed events; provider/mode/event ID dedupe and per-provider reconciliation |
| B4React BillingCardDialog | Stripe Elements and client secret | Capability-selected registration component, with no raw PAN/CVC on our server |
| useBilling/useSubscription | Stripe ID validation, Stripe host allowlists, shared account snapshot | Typed provider capability/checkout result; explicit safe host policies for each adapter, never unrestricted redirects |
| Invoice/profile UI | Stripe-shaped lines, default methods and receipt links | Common read model plus unsupported-action states; preserve native page family |
| Settings/config | STRIPE_ENABLED and Stripe keys/price IDs | Provider-specific secrets and enablement; separate test/live identities and health |

Provider interfaces should express operations such as catalog, register method, create
checkout, verify result, read snapshot, preview/apply change, invoices and webhook verify.
Capabilities must separately describe registration UI, recurring scheduling, proration,
period-end change, default method and portal support. Do not force Toss billing-key charges
to pretend to be Stripe-managed schedules. The domain service should own account locks,
request identity, tier policy, durable reservations and notification policy. No interface
or state library is added by this research.

## Coexistence and migration

Prefer optional new-customer routing while existing Stripe subscriptions renew on Stripe.
Persist the chosen provider with each attempt/subscription; a timeout must retry the same
provider instead of falling through and double-charging elsewhere. Define a cross-provider
one-active-subscription rule under an account lock before enabling routing.

A future migration needs provider/account/mode-scoped customer, method, subscription,
price, invoice and event references. Keep legacy Stripe IDs mapped during backfill; do not
rename a stripe ID into a supposedly interchangeable token. Preserve old invoice access,
refund/dispute handling, signed webhook delivery and cancellation history until obligations
are settled. Plan switching between providers requires a deliberate billing-boundary cutover,
verified cancellation and payment confirmation; it is not a normal plan-change API call.

Stripe's [export policy](https://docs.stripe.com/get-started/data-migrations/pan-export)
permits secure card-data transfer to eligible PCI DSS Level 1 processors through provider
teams; **Link credentials are excluded**. Subscription and payment-history objects are not
part of that credential export. Confirm destination import support and ID mappings; do
not promise token portability or handle raw exported cards in this application. Default
fallback is explicit re-registration with the new provider. Existing customers should
not lose access while a migration is unconfirmed.

## Conditional next steps

| Condition | Next decision / implementation work |
| --- | --- |
| Korean seller, domestic methods dominate | Compare direct Toss contract with a concrete PortOne PG/channel; prototype hosted registration and recurring charge recovery |
| Global software with outsourced customer tax/payment operations | Check Paddle product/country acceptance, payout and low-ticket economics; prototype checkout/portal/webhooks |
| No unmet payment need or unresolved seller requirements | Retain tested Stripe template; add no abstraction or provider |

If a provider is approved later, open a **separate implementation issue** with the selected
contract and sandbox scope: identity migration, capability contract, provider adapter,
verified webhooks/reconciliation/outbox, frontend registration/receipt differences,
no-double-charge tests, rollout/rollback, refunds/disputes and #95 email responsibility.
Required tests include same request twice, ambiguous timeout, out-of-order events, mode/owner
isolation, cancellation/upgrade payment failure, expired credentials and cross-provider
migration boundaries. No new account, commercial commitment, production charge/refund,
or sandbox PoC is needed for the current **defer adoption** decision.

Research completion does not resolve the merchant requirements marked 확인 필요. Revisit
this dated comparison after those decisions; public prices and acceptance rules can change.
