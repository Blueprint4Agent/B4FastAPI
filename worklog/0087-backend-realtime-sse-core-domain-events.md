# commit title
backend: add realtime SSE stream and core domain-event structure

# changed file scope
- src/backend/app/main.py
- src/backend/app/core/settings.py
- src/backend/app/core/realtime/*
- src/backend/app/routers/v1/events.py
- src/backend/app/services/realtime.py
- src/backend/app/services/api_key.py
- src/backend/tests/api/v1/events/test_events_api.py
- src/backend/.env.example
- docker/.env.example
- src/backend/BACKEND.md
- src/backend/README.md
- src/backend/TEST.md
- docs/ko/backend/BACKEND.md
- docs/ko/backend/README.md
- docs/ko/backend/TEST.md

# reason
- Introduce a realtime channel so authenticated clients can receive server-pushed events through SSE.
- Standardize realtime event ownership by moving service-specific event enums under `core/realtime/domain_events`.
- Keep transport-level concerns and domain event contracts clearly separated for future domains.

# impact
- New authenticated SSE endpoint is available at `/api/v1/events/stream`.
- Stream now emits `connected`, `ping`, and API key domain events via Redis Pub/Sub fan-out.
- API key create/status/delete operations publish realtime events to per-user channels.
- Backend docs and localized docs now include realtime architecture and project pattern (with Mermaid).
