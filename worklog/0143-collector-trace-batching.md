# Commit Title

perf(observability): batch collector trace exports

# Changed File Scope

- docker/observability/otel-collector.yml
- README.md and notes/ko/README.md
- worklog/0143-collector-trace-batching.md

# Reason

The Collector forwarded traces without a batch processor. Batch incoming spans
before exporting to Tempo and the debug exporter using the pinned version defaults.

# Impact

Enable the batch processor in the traces pipeline. Document the 200ms timeout and
8192-span send trigger, which is not a maximum batch size. Explain its independence
from the backend SDK BatchSpanProcessor and how to restart the Collector to apply it.
Running containers have not been restarted.

# Loop Alignment

Backend request lifecycle, domain event, background task, and frontend API state,
realtime refresh, desktop recovery, and UI composition loops are not applicable:
only the external trace collector configuration and documentation change.

# Verification

- make check passed (environment contract, lint/format, TypeScript and API contracts).
- git diff --check passed.
- Local tests were not rerun following the preceding test-skip instruction.
- No live Collector restart or trace delivery verification performed; GitHub CI remains enabled.
