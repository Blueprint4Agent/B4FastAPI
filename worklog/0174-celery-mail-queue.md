# Commit Title

refactor(backend): move authentication mail delivery to Celery

# Changed File Scope

Mail producer/consumer, Celery registration, API lifecycle, legacy queue removal,
settings/examples, deployment startup, tests and EN/KO guides. Auth service line
endings are normalized from CRLF to the repository-required LF while updating
its queue import; no other auth logic changes.

# Reason

The user requested migration of the current verification/reset email background
queue after the foundation audit exposed dequeue-loss and blocking retry delays.

# Design

Keep the service-facing async mail producer methods; publish JSON Celery tasks
with correlation and expiry metadata. Standalone workers execute existing SMTP
service methods, retry with bounded countdowns and archive exhausted failures in
a namespaced Redis hash keyed by task ID. Failure archive retries never re-send
SMTP. Remove API-owned BRPOP worker/bootstrap and obsolete timeout configuration.
Email-enabled Docker startup starts and checks the worker before the API; Beat
remains optional. Keep SSE, DB migration, and API SMTP validation in their existing
lifecycles. No API schema or SQL database migration. Document draining legacy
queues before deploying and SMTP at-least-once limitations.

# Verification Plan

Root verify-plan/verify with complete branch scope; targeted producer/worker tests
including success, retries, failed archival recovery, disabled email and expired
links; real Redis + worker + local SMTP capture smoke; deployment command fixtures.
Do not send real customer mail or mutate a live deployment.

# Impact

EMAIL_ENABLED now requires a standalone worker and real Celery Redis broker.
Old Redis envelopes cannot be consumed by Celery. Existing retry settings remain.
Failed payloads contain sensitive links and require restricted broker access.

# Loop Alignment

Auth service -> async mail producer -> broker -> standalone worker -> MailService.
Worker logs and persisted failure records expose completion/failure; no new SSE
domain event is needed for transactional email. API startup/shutdown no longer
owns worker tasks. Frontend loops are unchanged and not applicable.

# Verification

- `make verify-plan` and `make verify`: all selected backend and full
  frontend/integration groups passed. Full branch plan against
  672ca9af1d11ef73b61a1ac9c718a1546829ceb6 selected the same seven groups; the
  foundation's earlier checks and this follow-up together cover the branch.
- Final test-only SMTP-startup isolation change was followed by
  `make backend-check backend-test`: 105 passed, three existing deprecation warnings.
  Already-passed unchanged frontend checks were not repeated for that test edit.
- Real isolated Redis container + separate worker + local SMTP capture passed:
  both email types, transient failure/retry, exhausted failure archival, expired
  link suppression, trace propagation and token log redaction. No external SMTP
  or customer mail was used; test processes/container were removed.
- Deployment script tests verify local/external brokers, disabled mail/login,
  worker-before-API readiness and blocking API rollout on worker health failure.
- Compose example configuration and `bash -n docker/scripts/docker-up.sh` pass.
- No selected checks omitted. No production image rollout or legacy backlog
  mutation performed; real-process smoke used local solo rather than a deployed
  Linux prefork image. Upgrade/rollback drain procedures are documented.
- Git governance is validated using staged metadata and the updated ready PR.
  Required CI is rerun for the follow-up commit before merge.
- Request/background loops followed; connection-bound SSE remains in API.
  Frontend/domain-event loops are not applicable to mail delivery and were not
  intentionally bypassed.
