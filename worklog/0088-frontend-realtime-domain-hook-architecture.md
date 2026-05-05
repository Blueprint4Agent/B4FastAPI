# commit title
frontend: refactor realtime subscriptions into domain-based hooks and shared stream core

# changed file scope
- src/frontend/src/api/events/eventsApi.ts
- src/frontend/src/api/events/eventsError.ts
- src/frontend/src/hooks/api/events/useEventsApi.ts
- src/frontend/src/hooks/realtime/core/useRealtimeStreamSubscription.ts
- src/frontend/src/hooks/realtime/apiKey/useApiKeyRealtimeSubscription.ts
- src/frontend/src/realtime/logging.ts
- src/frontend/src/pages/settings/SettingsPage.tsx
- src/frontend/src/tests/component/pages/settings/SettingsPage.test.tsx
- src/frontend/src/api/generated/openapi.ts
- src/frontend/FRONTEND.md
- src/frontend/README.md
- docs/ko/frontend/FRONTEND.md
- docs/ko/frontend/README.md

# reason
- Realtime logic was page-heavy and partially coupled to API-layer paths, which makes scale-out difficult when additional domains subscribe to SSE.
- A core stream lifecycle hook and domain-scoped realtime hook layout was needed to keep shared transport concerns separate from domain event parsing.

# impact
- SSE stream connect/reconnect/error handling is centralized in `hooks/realtime/core`.
- API-key-specific event filtering/dispatch is isolated under `hooks/realtime/apiKey`.
- Page layer now consumes domain realtime hooks and focuses on UI state updates only.
- Service-event logs are standardized while excluding heartbeat/system events.
