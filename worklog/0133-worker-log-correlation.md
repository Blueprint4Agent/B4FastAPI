# Commit Title

fix(observability): correlate worker logs with queued tasks

# Changed File Scope

- Backend task log context helper, logging factory/filter, and Redis queue worker.
- English/Korean backend engineering guides.

# Reason

Queued jobs retained originating trace IDs but did not bind them to logs during
handler execution, retries, or DLQ processing.

# Impact

Bind task_id and originating trace_id around envelope processing, including observers
and retry handling. Restore prior context on return, error, and cancellation.
Generate missing task IDs and retain them in retried envelopes. Missing trace IDs
remain empty instead of inheriting another request/job. Task INFO/WARNING output
includes correlation IDs; HTTP log visibility policy remains unchanged.
Share record population between the logging factory and filter. This is log correlation
only: no OTel parent span propagation or delivery guarantees are added.

# Verification

make backend-check and make contract-check passed.
METRICS_ENABLED=true make backend-test: 70 passed, 3 existing deprecation warnings.
METRICS_ENABLED=true is used for
the test process because local .env disables /metrics required by existing tests.
Dedicated concurrency/cancellation assertions and live distributed trace export
are not covered by this change.

# Loop Alignment

Background task loop remains enqueue -> worker handler -> retry/DLQ and observers;
log context encloses this lifecycle and resets afterwards. Request lifecycle and
domain event logic remain unchanged. Frontend loops are not applicable.
