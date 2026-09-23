# B4 API contract baseline

This directory records the existing HTTP contract for a shared React frontend and
alternative backend implementations. `openapi.json` is the versioned baseline;
this document covers behavior that TypeScript generation cannot express.
Korean: [notes/ko/contracts/README.md](../notes/ko/contracts/README.md).

## Ownership and regeneration

During this transition, FastAPI route/model declarations are the authoring source.
Do not edit `openapi.json` or `src/frontend/src/api/generated/openapi.ts` manually.
The export uses OpenAPI 3.1 and the current API version `0.1.0`; it does not start
the lifespan, run migrations, or connect to DB/Redis. The exported title is fixed
to `B4 API` so deployment branding does not alter the baseline.

From the repository root:

```sh
make contract-export
make frontend-api-generate
make contract-check
make frontend-typecheck
make check
make test
```

`contract-check` compares the backend export with the snapshot; it is not a
cross-backend compatibility test or a generated-TypeScript drift check. The existing
`npm run generate:api` still fetches the running server; use the baseline generation
command above for this shared contract. Optional generation fallback is a local
convenience and is not evidence that a contract is current.

Changes to paths, methods, field names, required/null behavior, status codes,
security requirements, or event payloads must be reviewed with both consumers and
providers. Preserve current operation IDs/component names when possible. An
added error enum can require updates to exhaustive frontend message maps even
when the HTTP change otherwise appears additive. Future Spring Boot support must
pass the same behavioral scenarios; publishing this file alone is insufficient.

## HTTP and errors

- Domain APIs use `/api/v1`; `/config`, `/health/live`, and `/health/ready` are also
  public frontend-facing contracts. API JSON field names use the published spelling,
  including `snake_case`. Dates/times use the schemas' `date-time` strings. Preserve
  each field's optional/null distinction and integer representation.
- Protected routes accept Bearer JWT or `X-API-Key`. If both are supplied, a bad
  Bearer token is not ignored; valid identities must belong to the same user.
  API-key authentication checks expiry/revocation and records usage.
- Domain errors use `{ "detail": { "error": "CODE", "message": "...", "details": {} } }`;
  `details` may be absent/null. A status shared by Auth and API Key errors is an
  `anyOf` of their response models, not an overwritten response declaration.
- Request validation uses HTTP 422 and FastAPI's `HTTPValidationError` shape.
- Unexpected errors before a response starts use HTTP 500 with
  `{ "error": "INTERNAL_ERROR", "message": "An unexpected error occurred." }`.
  Domain 500 responses retain their `detail` envelope. This baseline deliberately
  describes both existing shapes. Framework routing failures such as unknown
  paths/methods are outside the domain-error contract.
- Request correlation headers are `X-Request-ID` and `X-Trace-ID`.

## Authentication, cookies, and OAuth

- `POST /auth/login` (under `/api/v1`) accepts JSON, returns access/refresh tokens
  and the user, and sets two separate cookies: `template_refresh_token` and
  `template_refresh_sid`. The SID is supplied through a cookie, not the JSON response.
- Both cookies use `HttpOnly`, `Path=/`, and no explicit Domain. HTTPS uses Secure
  and SameSite=None; HTTP uses SameSite=Lax. HTTPS detection honors the first
  `X-Forwarded-Proto` value, so the deployment proxy must control that header.
- `remember_me=true` adds persistent expiry; false creates browser-session cookies.
  Server refresh-session TTL is `REFRESH_TOKEN_EXPIRE_DAYS` in both cases.
- `POST /auth/refresh` accepts optional JSON `refresh_token`, `session_id`, `user_id`.
  Non-empty token/SID fields take precedence over cookies. A missing user ID is
  resolved from the stored SID. Browser clients can send `{}` with credentials.
- Successful refresh issues an access token, retains the existing refresh token
  and SID, extends server TTL, and reissues cookies according to the stored
  remember-me setting. This is **not refresh-token rotation**.
- Logout invalidates **all refresh sessions for that user** and expires both
  cookies. Previously issued JWT access tokens are not revoked by logout.
- `/auth/token` accepts OAuth2 form data for token tooling. It returns tokens but
  does not set browser refresh cookies; use `/auth/login` for browser login.
- OAuth start returns 307 plus Location to the provider. Callback success returns
  307 to `APP_BASE_URL` + success path and sets persistent refresh cookies.
  Provider/domain failures redirect to the failure path with `error` and, for
  domain failures, `message` query parameters. Invalid provider enum/query input
  can still produce 422 before the handler; unexpected errors can produce 500.
- CORS must allow the actual web/Tauri origin with credentials. Proxy-generated
  callback URLs must preserve the public scheme/host.

## Configuration and readiness

- `/config` exposes login/email/OAuth flags and provider names. When login is
  disabled, startup may supply a bootstrap user/access token. Clients must not
  treat a failed config fetch as `login_enabled=false`.
- `/health/live`: 200 `{ "status": "ok" }`.
- `/health/ready`: 200 when `status=ok`, 503 when `status=degraded`; `checks`
  includes database/redis results (`ok` or `failed` in the current implementation).
  A replacement backend must provide the public readiness adapter used by Tauri.

## SSE event contract

- `GET /api/v1/events/stream` returns `text/event-stream`, never a JSON document.
  The frontend uses fetch streaming with Authorization and credentials.
- Each frame uses `id`, `event`, and a JSON `data` field; the connected frame
  additionally supplies `retry` in milliseconds. Heartbeats use `ping`.
- JSON data contains `id`, `type`, `version` (currently `v1`), `ts`, and `payload`.
  The OpenAPI media-type extension `x-sse-event-schema` points to
  `RealtimeStreamEvent`; the HTTP body itself remains a string stream.
- `connected`: payload `{ user_id, channel }`. Treat channel as an opaque value.
- `ping`: currently an empty payload.
- `api_key.created`, `api_key.status_updated`, `api_key.deleted`: payload
  `{ api_key: APIKeyResponse }`. Raw API-key secrets are never event payloads.
- `RealtimeEvent` describes the generic envelope, while `RealtimeStreamEvent`
  and `APIKeyEvent` describe known event types. Frontend types are generated from
  these schemas. Unknown event types can be ignored for forward compatibility.
- Delivery uses live pub/sub, not a durable log. Last-Event-ID is accepted for
  diagnostics only; there is no replay or exactly-once guarantee. Once a stream
  starts, failures close it rather than returning a JSON error/status change.

## Known follow-up work (not guarantees of this baseline)

- Browser SSE reconnect currently does not guarantee a fresh REST snapshot;
  disconnected clients can miss changes. Add resource revalidation on reconnect
  before claiming loss recovery. Desktop session recovery alone is insufficient.
- On failed refresh, the router attempts cookie deletion on its injected response,
  but the global exception handler creates another response. Cookie deletion is
  not currently guaranteed on this failure path.
- Generated TypeScript is not runtime payload validation. The existing API-key
  event consumer only partially checks incoming records.
- Independent frontend packaging, automated CI drift gates, Spring Boot provider
  tests, database migration portability, and live stack switching are later work.
