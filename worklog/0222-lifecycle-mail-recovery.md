# Commit Title

fix(mail): bound lifecycle retries and expose safe recovery

# Changed File Scope

Lifecycle mail repository/service/webhook policy, operator CLI, existing mail queue integration, backend tests and English/Korean operation guides.

# Reason

Issue #95 already has an encrypted deletion-atomic outbox and lifecycle templates, but crashed workers can exceed the retry budget, failures have no supported retry interface, and billing locale/event boundaries need verification.

# Design

Reuse MailQueueService publication and MailService/HTML templates through the existing Celery outbox task. Bound all worker claims including abandoned leases to five; preserve terminal failures and allow explicit operator retry only before the original 72-hour expiry. List metadata only with no decrypt capability. Existing deployment-operator CLI boundary, no manager/admin HTTP endpoint. Signed billing events confirm provider state, use event identity for applied changes, suppress stale initial-invoice plan messages, and resolve supported locales from provider preferences. Deletion completion remains atomic with deletion and separate from proof-code email. No API/DB schema changes intended.

# Verification Plan

DB-backed retry/lease/retention/operator tests, signed event/locale/outbox tests, deletion transaction and no-broker failure tests, English/Korean HTML/plaintext tests. Root make backend-format, make verify-plan and make verify; run CLI help without modifying live jobs. No external SMTP/payment side effects.

# Impact

No automatic resend of terminal jobs; authorized local operators explicitly retry within retention. A worker crash after SMTP acceptance still permits duplicate delivery; no exactly-once promise. No additional app receipt/renewal/failure emails, avoiding Stripe duplication.

# Loop Alignment

Existing service/repository transaction and signed webhook request lifecycle retained. Background recovery uses existing Beat scan and worker drain with bounded lease recovery. No new frontend, realtime or desktop loop needed for server-only notifications. Documentation records provider-state vs outbox transaction boundaries.

# Verification

- Focused mail/billing/deletion integration: 65 passed. Root selected full backend suite: 418 passed (existing dependency/resource warnings).
- make backend-format and git diff --check passed; operator CLI --help verified without accessing live jobs.
- make verify-plan then make verify passed. Classifier selected backend=True/frontend=full because shared test isolation and a new CLI are protected/unknown scope.
- Hook fixtures, project init/architecture/environment/Ruff/backend/contract checks, branding, frontend integration packaging and project build fixtures passed. Unchanged child check/test/UI/route/style-studio results reused through content-bound local receipts; no manual downgrade or bypass.
- No frontend source/pin or OpenAPI schema changes; no migration as model columns are unchanged. No new frontend realtime/desktop/UI loop applies.
- Only test data and mocked SMTP/Stripe/broker were used. Real webhook/SMTP and deployment activation remain separate operational checks; no emails/payments were sent.
- Bilingual backend/Celery and mail operations docs synchronized. Planned and actual PR governance required before merge.
