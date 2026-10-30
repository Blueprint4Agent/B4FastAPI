# Cookie refresh CSRF protection

Browser refresh uses a synchronizer token tied to the Redis refresh session:

1. Request `GET /api/v1/auth/csrf` with credentials and `X-CSRF-Bootstrap: 1`.
2. Send the returned `csrf_token` as `X-CSRF-Token` on `POST /api/v1/auth/refresh`.
3. Missing, invalid or another session's proof returns `403 CSRF_INVALID` before renewal.

Both successful responses use `Cache-Control: no-store`. Never log or persist the proof.
The frontend keeps it request-local and bootstraps on every refresh, including reload,
OAuth return and desktop/session recovery. This adds one request per refresh, with no
retry loop or second session store. A failed bootstrap stops refresh.

The bootstrap validates both HttpOnly refresh cookies and requires a custom header,
forcing cross-origin browsers through CORS preflight. Configure `CORS_ORIGINS` with
only trusted frontend origins; do not allow arbitrary origins or untrusted subdomains.
HTTPS cookies still use `Secure; HttpOnly; SameSite=None` for separate-site deployments.
This policy relies on the browser's same-origin/CORS enforcement for token disclosure.
HttpOnly does not itself prevent CSRF, and CSRF tokens do not protect against XSS.

CSRF state is a random 256-bit secret under `refresh_csrf:<session_id>`. Concurrent
bootstrap calls reuse one value via Redis SET NX. Existing sessions initialize lazily
without extending their TTL. Refresh extends the proof TTL alongside the session;
logout/account revocation removes both. No SQL migration or forced logout is required.

Only complete explicit JSON `refresh_token` and `session_id` credentials bypass the
CSRF check. Partial input that falls back to either cookie still requires a proof.
Bearer/API-key authenticated routes retain their existing authentication. This change
does not add login-CSRF protection to password login or change OAuth state binding.

Roll out the matching frontend and backend together. Older browser clients without
this handshake will receive 403 on refresh. Keep backend Origin validation and login
CSRF review as separate follow-ups; they are not claimed as implemented here.

[한국어](ko/csrf.md)
