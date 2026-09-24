# Commit Title

fix(observability): clarify mail and worker log ownership

# Changed File Scope

Mail service, mail queue handlers, generic worker retry logging, and English/Korean
backend engineering guides.

# Reason

Queued provider failures were logged twice with stacks, and scheduled retries used
the same severity as final failure. Mail completion was also logged twice at INFO.

# Impact

MailService propagates failures without logging when raise_on_failure=True, but retains
ERROR stacks when swallowing direct-send failures. Attempts use DEBUG. MailService owns
provider completion INFO; duplicate mail queue completion logs are removed. Generic
worker completion stays DEBUG, retries become WARNING without stacks, and DLQ moves
retain ERROR with stacks. Task/trace context and retry/delivery behavior are unchanged.

# Verification

make backend-check and make contract-check passed.
METRICS_ENABLED=true make backend-test: 70 passed, 3 existing deprecation warnings.
METRICS_ENABLED=true is supplied only
to the test process because local .env disables /metrics required by an existing test.
No dedicated logging assertions or live SMTP/queue delivery tests were added.

# Loop Alignment

Background task loop and domain side effects remain unchanged; only log ownership and
severity change. Request response behavior is unchanged. Frontend loops are not applicable.
