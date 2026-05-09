# commit title
backend: refine logging context visibility policy

# changed file scope
- src/backend/app/core/logging.py

# reason
- INFO-level logs should stay concise in normal operation.
- Request/trace identifiers are still needed for production error investigation.

# impact
- DEBUG mode keeps detailed logger/context output.
- Non-debug mode keeps concise output and includes request_id/trace_id only for ERROR+ logs.
- Logger name normalization is preserved for clear module-oriented log labels.
