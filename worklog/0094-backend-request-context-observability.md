# Backend Request Context Observability

- commit title: backend request context observability
- changed file scope: `src/backend/app/core/request_context.py`, `src/backend/app/core/logging.py`, `src/backend/app/main.py`, `src/backend/app/core/task_queue/services/mail.py`, backend docs, localized backend docs, request context/logging tests
- reason: add the first observability foundation so each HTTP request has stable correlation identifiers across responses, logs, and queued mail jobs
- impact: responses now include `X-Request-ID` and `X-Trace-ID`; inbound request ids are preserved; W3C `traceparent` trace ids are accepted; backend logs receive request and trace context through a consistent key-value prefix; mail queue jobs inherit the current trace id
