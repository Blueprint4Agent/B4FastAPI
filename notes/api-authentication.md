# API authentication policy audit

Korean: [API 인증 정책 점검](ko/api-authentication.md).

This inventory describes this repository's current policy, not an industry requirement.
An application API key (`X-API-Key`) and the backend's Stripe key are different credentials.
Stripe keys belong only in backend configuration and do not authenticate callers to this API.

| Operation (under `/api/v1`) | App API key | Additional requirement |
| --- | --- | --- |
| `GET /billing/config` | Accepted | Active owner |
| `POST /billing/setup-sessions` | Accepted | Active owner |
| `GET /billing/setup-sessions/{session_id}` | Accepted | Owned Stripe session |
| `GET /billing/payment-methods` | Accepted | Only own methods |
| `POST /auth/me/deletion-code` | Rejected (401) | Bearer session, enabled login/email, issuance limits |
| `DELETE /auth/me` | Rejected (401) | Bearer, matching email, one-time code, last-admin protection |
| `GET /auth/admin/users` | Accepted | Key owner must currently have admin role; otherwise 403 |
| `GET /auth/admin/user-role-stats` | Accepted | Key owner must currently have admin role; otherwise 403 |
| `GET/PATCH /auth/me` | Accepted | Active owner |
| API-key create/list/delete/status | Accepted | Only own keys |
| `GET /events/stream` | Accepted | Only own event channel |
| `POST /auth/logout` | Accepted | Clears owner's refresh sessions; access JWTs expire normally |

Exactly two operations are bearer-only; the two admin operations accept keys and independently
check the owner's current database role. Keys do not have billing or other endpoint scopes.
They currently also allow profile edits, management of the owner's other keys and logout.
Billing now accepts that same owner authority; account deletion remains bearer-only.

When both bearer and API key are supplied to an operation accepting either, both must be
valid and identify the same user. An expired/invalid bearer can cause 401 even with a valid
API key; conflicting users cause 403. Bearer-only operations do not inspect X-API-Key.

`POST /auth/refresh` is a separate refresh-token/session exchange. API-key or access-token
authentication alone is insufficient; it uses JSON or refresh cookies. Signup/login, email
verification/reset and OAuth have their own password, one-time-token, state or feature checks.
The absence of an OpenAPI security lock does not mean those checks are absent.

Swagger uses OAuth2PasswordBearer for sessions: Authorize with the application's email as
username and account password to call `/auth/token`. APIKeyHeader uses the app key value
as X-API-Key. Locks indicate an authentication scheme, not a successful permission check.
An APIKeyHeader authorization does not authorize the separate bearer-only scheme.
Swagger security declarations match the audited guards; business role/feature checks can
still reject authenticated calls. The shared INVALID_TOKEN message currently says
"Invalid refresh token" even when a bearer-only guard rejects an API-key-only request;
use the credential scheme and error code to diagnose that case.

Evidence: `app/deps.py`, the auth/billing/API-key/events routers, runtime OpenAPI, and
`tests/integration/api/v1/auth/test_api_auth_policy.py`. Tests issue real application keys
in an isolated SQLite database, check both bearer-only operations and all twelve billing key guards, test both admin role
outcomes, exercise accepted operations and verify the exact OpenAPI exception inventory.
No production user or real account is changed by these tests. Billing key access is covered by the real-key registration and ownership integration tests.
