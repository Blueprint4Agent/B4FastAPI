# Commit Title

fix(observability): classify global exception log severity

# Changed File Scope

Backend error_logging.py severity policy, main.py global handlers, and English/Korean
backend engineering guides.

# Reason

Expected client/domain rejections were logged at ERROR alongside server failures.

# Impact

Domain 5xx remain ERROR. Explicit authentication/security codes and HTTP 429 use
WARNING. Other domain 4xx use INFO. The existing HTTPException fallback uses
WARNING for 401/403/429 and INFO for other 4xx. Unexpected errors retain stack traces.
HTTP statuses, bodies, error codes, and handler registration are unchanged.
OAuth redirect logs, mail/worker logging, and existing context visibility are unchanged.

# Verification

make backend-check and make contract-check passed.
METRICS_ENABLED=true make backend-test: 70 passed, 3 existing deprecation warnings.
METRICS_ENABLED=true applies only to the test
process because the local .env disables /metrics required by an existing test.
No dedicated severity-policy tests were added.

# Loop Alignment

Request lifecycle preserves exception propagation and response mapping. Domain event,
background task, and frontend loops are not applicable: no corresponding behavior changed.
