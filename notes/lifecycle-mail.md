# Lifecycle email delivery and recovery

[한국어](ko/lifecycle-mail.md). Issue #95 follows the [billing audit](billing-audit-93.md).
Existing migration 0011 is required; this change does not alter the schema.

## Event policy

| Trigger | Recipient and confirmation | Message |
| --- | --- | --- |
| Initial `invoice.paid` | Active local account email; signed matching mode/customer; paid initial invoice with a single complete line whose price matches the current active subscription | Subscription started |
| `customer.subscription.updated` | Active local account email; actual old/new price transition, currently active and no pending update; current provider price still matches | Plan applied |
| `customer.subscription.deleted` | Active local account email; canceled for cancellation_requested and no replacement nonterminal subscription | Plan changed to Free |
| Account deletion | Email captured from the authenticated account; deletion proof verified; outbox and user deletion in one DB transaction | Account deleted |

Cancellation **reservation**, restoration, payment failure, authentication required,
renewal, a return URL, pending upgrades and unknown prices do not send app lifecycle
mail. These remain state synchronization inputs where documented in the billing guide.
An invoice with missing/ambiguous/truncated lines or a stale initial price is suppressed;
Stripe's financial receipt remains authoritative. Complex billing products require a
separate policy before enabling lifecycle mail for them.

Stripe owns financial receipts, renewal reminders and failure/action-required recovery.
The app owns the above account/plan notices. Review Dashboard customer email and revenue
recovery switches before launch; they are account settings, not guaranteed defaults.
If enabling provider cancellation notices, choose one owner for completion messaging.
The application does not attempt to disable provider emails through the API. See Stripe
[receipts](https://docs.stripe.com/receipts) and
[customer emails](https://docs.stripe.com/billing/revenue-recovery/customer-emails).

Billing language is the first supported `ko`/`en` entry (including region suffixes) in
the current Stripe Customer `preferred_locales`, otherwise English. It is captured in
the encrypted payload at reservation. Configure that preference on the provider customer;
changing the app's display language alone does not persist it to Stripe. Deletion uses
the confirmed request's Accept-Language. Both subjects, HTML, plaintext and CTA/fallback
links are localized: billing points to `/settings?section=billing`, deletion to `/home`.
Deletion proof-code mail is separate and has no completion CTA.

## Consistency and deduplication

MailQueueService wakes the existing Celery `b4fastapi.notifications.drain` task with an
empty broker payload; MailService and existing branded templates perform delivery.
Beat scans every minute, so broker wake-up failure does not lose committed reservations.
Run one Beat and a worker. SMTP delivery never occurs in an HTTP request.

Deletion and reservation commit atomically: a failed outbox insert rolls back deletion.
After commit, Redis cleanup/broker failures cannot restore the user or lose the outbox.
For billing, Stripe and the DB cannot share a transaction: the signed webhook fetches
current provider state, commits synchronization and then inserts the outbox before
acknowledging success. A failure before reservation returns non-2xx for provider redelivery.
There is no direct mutation-to-email dual write. An obsolete event is intentionally
suppressed; Beat repairs subscription state, not missing historical notification events.

Start/end keys are subscription-semantic; applied changes use subscription + event ID,
not seconds-resolution timestamps, so repeated transitions in a second are not collapsed.
Exact event redelivery is deduplicated. Legacy timestamp/price keys are recognized to
avoid replaying historical messages at upgrade. Deploy the producer version consistently;
rolling old/new producers concurrently cannot provide cross-format atomic deduplication.
Distinct Stripe event IDs for the same semantic change can still produce separate notices;
there is no universal exactly-once event or SMTP guarantee. Stripe's
[event-order guidance](https://docs.stripe.com/webhooks#event-ordering) explains ordering
and duplicate handling. Current-state validation suppresses obsolete plan events.

## Retry, retention and access

Each automatic attempt acquires a five-minute lease. At most five claims are made,
including crashed workers that never call completion. SMTP errors back off by
2, 4, 8 and 16 minutes; the fifth failure is terminal. Abandoned fifth leases become
`failed / delivery_unconfirmed`; SMTP exceptions become `failed / delivery_failed`.
Old lease holders cannot overwrite a later claim/result. Logs contain only job ID,
attempt, safe error category and operator identity, never provider exception text or recipients.

Payloads use Fernet authenticated encryption with a domain-separated SHA-256 key derived
from SECRET_KEY. New deletion messages retain only email and locale inside the cipher;
billing also retains greeting name and plan label. No user FK is required after deletion.
Only API/worker processes and trusted deployment operators with DB/key access may read
this storage; restrict DB accounts, filesystem, logs and backups accordingly. Broker
messages contain neither recipient nor ciphertext.

Success or disabled delivery immediately clears ciphertext. Other recipients expire
72 hours after reservation, including failed jobs; every scan erases expired payloads.
No delivery or manual retry is permitted beyond the deadline. Physical erasure occurs
on the next scan, so a stopped Beat/worker delays deletion; monitor the scan and run it
after recovery. Backup copies follow the deployment's restricted backup retention policy;
this worker cannot erase external backups. Drain pending mail before rotating SECRET_KEY.

Opaque dedupe IDs and kind/state/attempt/error/expiry metadata are retained indefinitely
without recipient payload, so historical event replay cannot regenerate erased recipients.
Explicit retry resets the attempt budget but **never** extends the original expiry.
Operator log retention is deployment-owned; export these logs to retain retry history.
SMTP acceptance followed by worker death can duplicate delivery; inspect mail-provider
logs before retrying an ambiguous failure.

## Operator commands

From the repository root (read-only list; retry changes one retained failure):

```sh
cd src/backend
uv run python -m app.manage_notifications list --limit 50
uv run python -m app.manage_notifications retry <64-character-notification-id>
```

List returns only safe metadata, at most 100 rows ordered newest expiry first. Retry
rejects disabled email, invalid IDs, expired/erased/sent/skipped/pending/sending records.
It logs the OS operator and result, commits pending state, then the next Beat scan
publishes delivery. The command never decrypts a payload or sends SMTP directly.
This is the same deployment-operator boundary as the role CLI, not an application
manager/admin permission. No user, manager or admin HTTP endpoint for cross-account
mail inspection/retry is introduced. Do not grant shell/DB access through app roles.

Email-disabled queueing is a no-op. Already-queued deliveries are skipped and erased;
account deletion remains protected by its existing email-code requirement and is blocked
when email is disabled. SMTP/broker/worker outages after completed domain work never
undo that work. Unknown-key decryption failures consume the bounded delivery budget.

## Verification

DB integration covers crash exhaustion, stale leases, SMTP retries and manual recovery,
original expiry, erasure, metadata privacy, deletion rollback and broker failure.
Signed webhook tests cover duplicated/obsolete/same-second events, cancellation with
replacement subscriptions, initial invoice formats and provider locale selection.
Template tests cover both languages, escaping, plaintext and CTA/fallback links.
No external mail or real payment is sent. See [worklog](../worklog/0222-lifecycle-mail-recovery.md)
for root Make results. External webhook/SMTP/worker deployment checks remain mandatory
before production; a local passing test does not activate them.
