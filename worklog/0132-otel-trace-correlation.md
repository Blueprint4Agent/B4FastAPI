# Commit Title

fix(observability): align log and response trace IDs with OpenTelemetry

# Changed File Scope

- Backend request context helper and tracing middleware-order comment.
- English/Korean backend and behavioral contract guides.

# Reason

Independently generated correlation IDs could differ from the active OpenTelemetry
trace ID and prevent users from locating a request's trace using its logs.

# Impact

Prefer a valid active span context for log records and X-Trace-ID response headers,
including unsampled spans. Retain existing header/generated-ID fallback when there
is no active span. X-Request-ID behavior is unchanged. No OpenAPI schema changes.
An ID does not guarantee trace export; queue propagation remains separate work.

# Verification

make backend-check and make contract-check passed.
METRICS_ENABLED=true make backend-test passed: 70 tests, 3 existing deprecation warnings.
METRICS_ENABLED=true is supplied only
for the test process because local .env disables the endpoint expected by existing tests.
Live Collector/Tempo/Grafana delivery and dedicated tracing-enabled integration cases
were not verified in this change.

# Loop Alignment

Request lifecycle remains router -> dependency -> service -> response. This change
only resolves correlation metadata. Domain event and background task loops are not
applicable; no publishers, workers, queues, or frontend code changed.
