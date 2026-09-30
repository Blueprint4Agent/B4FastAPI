# Commit Title

feat(auth): add welcome mail and verified account deletion

# Changed File Scope

Backend auth service/repository/router/dependencies, token utilities, Celery mail
producer/worker/templates, SQLite migration, OpenAPI contract, tests and EN/KO guides.
Frontend integration follows in the same task PR after the child PR merges.

# Reason

Complete onboarding with a greeting and let users delete their account only after
proving access to the registered mailbox. Email-address typing alone is not proof.

# Design

Email activation and first OAuth creation enqueue the existing Celery mail task.
Deletion-code requests require a bearer session, use the registered recipient only,
and enqueue the same mail pipeline. Redis HMAC challenges expire after ten minutes,
are consumed atomically, permit five incorrect attempts per ten-minute window and
five sends per hour with sixty-second spacing. Resend never resets failed attempts.
DELETE /auth/me requires email plus code, deletes owned data transactionally and
revokes tokens/cookies; API keys cannot authorize deletion. Last-admin deletion
shares the role-command lock and is rejected. SQLite AUTOINCREMENT migration avoids
reusing JWT subjects; PostgreSQL sequences remain unchanged.

# Verification Plan

Root make verify-plan / make verify, backend checks/tests and contract validation;
exercise expiry/replay/concurrency/throttling, OAuth greeting, data deletion and
populated SQLite upgrade/downgrade. Complete selected frontend checks with child work.

# Impact

Deletion is irreversible and requires enabled email delivery plus Redis. Greeting
publication failures are logged without undoing activation; this change does not add
an outbox. SMTP retains the existing at-least-once delivery limitations. Apply 0007
before serving deletion; ordinary application rollback needs no schema downgrade.

# Loop Alignment

Request lifecycle follows router -> service -> repository/util and typed errors.
Background work uses the existing Celery publication/retry/archive path. No new
realtime event: the deleted DB principal immediately fails authentication and the
initiating UI clears its session; other sessions fail on their next auth request.

# Verification

Root classifier selected backend plus full frontend/integration verification.
Project-init checks/tests, backend architecture and env contract passed through
make verify. make backend-check backend-test contract-check passed: 117 tests,
Ruff, contract snapshot/child agreement, populated SQLite upgrade/downgrade/re-upgrade.
After adding OAuth and API-key denial coverage, the focused root backend-test hook
passed all 16 selected tests (including the new OAuth case). Child checks are recorded
in its worklog; root packaging/custom-brand project-build tests also passed. No
required selected check was downgraded; unchanged passing groups were not repeated.
Live local Celery worker startup succeeded; SMTP logged delivery of the user's already
queued deletion-code request. No account was deleted by these verification actions.
