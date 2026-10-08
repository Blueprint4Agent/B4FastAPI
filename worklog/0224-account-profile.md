# Commit Title

feat(auth): add account security and personal profiles

# Changed File Scope

Auth profile schemas, persistence and API contracts; standalone profile and account settings UI, translations, tests and bilingual guides.

# Reason

Resolve B4FastAPI #92 by separating personal presentation from account security.

# Design

Profile lives at /profile in the persistent AppShell, with dropdown/account navigation, photo overlay and a modal with photo controls. Password change opens a modal. Both surfaces reuse the subscription snapshot. Country/region linked dropdowns store validated catalog IDs. Reuse GET/PATCH /auth/me and managed photo operations. Add nullable bio/location and migration 0016. Bearer-only password change requires a purpose-bound emailed code with expiry, retry/attempt budgets and revokes refresh sessions. Email-disabled operations fail closed. Personal profile only; no public lookup.

# Verification Plan

Run root make verify-plan then make verify. Cover ownership, validation, persistence, password failures and success; browser profile/account and General peer at mobile/desktop in both themes.

# Impact

Apply migration before rollout. Existing accounts have empty optional profile fields. Photo storage remains unchanged.

# Loop Alignment

Router/service/repository and page/hook/API loops retained. AuthProvider owns saved snapshot and desktop recovery. Reuse the existing Celery mail task with a password-change mail kind. No new realtime events: explicit mutations/reload refresh personal data; no cross-client live profile guarantee.

# Verification

Root `REDIS_IN_MEMORY=true make verify-plan` selected backend + full frontend because auth/contracts/shared UI changed. `make verify` passed: 435 backend tests, 147 frontend tests, 188 Chromium UI cases (including all 19 account/profile cases), 9 production-route cases and 3 Style Studio cases, plus static policy/type/format, contract, packaging and project-build checks. Focused account-profile run also passed 12/12. No classifier-selected checks omitted. Browser APIs were isolated fixtures; actual SMTP delivery and native desktop packaging were not exercised because this task adds neither SMTP configuration nor native code. Existing desktop recovery owner is unchanged.

Reviewed screenshots at 390/1440px in light/dark and compact-name/compact-bio captures. Repeated spaces preserve name width and 96px Bio editor height; country menus retain document height and scroll internally. Migration status locally reports 0016_personal_profile head.




## Local worker recovery

Runtime report: password-change mail was accepted by API but not delivered. Docker worker `b4fastapi-local-worker-celery-worker-1` still exposed only the four old MailKind values; its logs archived the new jobs as `invalid_payload`, while an account-deletion mail delivered successfully. Updated its four mail implementation files, restarted it, and verified the new kind and Celery ping. Rebuilt the existing `blueprint4fastapi:celery-local` image with the same mail updates so recreation retains support. No credentials, verification codes or recipients were printed. Archived requests were not replayed because their codes can be stale; a fresh password-change request logged successful SMTP delivery at 2026-10-08 12:13:43 UTC, and the user confirmed receipt.


## Follow-up verification flow

Add a separate authenticated, attempt-limited code check for password/deletion. Checking does not consume or extend a code; final action atomically validates/consumes it again. Resend cooldown is 30 seconds; latest issuance resets its 600-second TTL and invalidates the old code. UI requires successful verification and resets it on editing/resend/failure.

Latest follow-ups preserve navigation family, add configurable profile keyboard navigation, signup password/confirmation conditions, transparent icon showcase examples and reduced-motion-aware profile entrance. The final non-consuming verification transaction additionally queues a read to retain WATCH/MULTI protection; six focused challenge tests passed after this refinement.
