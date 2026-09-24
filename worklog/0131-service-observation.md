# Commit Title

refactor(backend): centralize API key service observation

# Changed File Scope

- app/core/observability/service.py: async observation decorator.
- app/services/api_key.py: four service operations; normalize line endings to LF.
- Backend engineering guides in English and Korean.

# Reason

Centralize service timing and outcomes using the existing OpenTelemetry SDK, with
minimal lifecycle code and DEBUG completion logging.

# Impact

API Key create/list/delete/status methods receive optional service spans. SDK context
management replaces manual lifecycle handling. Span names and native timestamps
avoid duplicate operation/duration attributes. Only outcome and error code are custom
attributes. Successful spans retain UNSET status. Arguments, results, exception
messages and stack traces are not captured by the decorator. Exceptions and cancellation
propagate; telemetry implementation errors are not silently suppressed.
Existing operation entry/completion logs are replaced; domain rejection logs remain.
No metrics, API contract, transaction, event delivery, or frontend changes.

# Verification

- make backend-check: passed.
- make contract-check: passed.
- Initial make backend-test: 69 passed, one existing metrics test failed because
  local .env disables METRICS_ENABLED and /metrics returned 404.
- METRICS_ENABLED=true make backend-test: 70 passed (3 existing deprecation warnings).
- No new tests added; live Grafana/Tempo delivery and dedicated cancellation/span
  assertions were not verified.

# Loop Alignment

Request lifecycle and domain event order are preserved: observation wraps existing
service execution including awaited publication. Background task loop is not applicable
because no worker or queue code changes. Frontend loops are not applicable.
