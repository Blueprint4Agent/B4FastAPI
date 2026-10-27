# Commit Title

refactor(backend): isolate database operations in repositories

# Changed File Scope

Backend services/models and auth DI; AGENTS.md and English/Korean backend guides/READMEs.
Existing profile-photo failure fixture may adopt the repository error contract.
No automatic checker, verification target or new test is added.

# Reason

Services directly query a DB session and interpret SQLAlchemy failures, while the
harness documents ambiguous Service-to-DB access. Keep Redis out of this change.

# Design

Move reconciliation selection, auth-DI API-key usage writes and SQLAlchemy error
interpretation to repositories.
Keep domain error codes and HTTP contracts stable. Expose a photo persistence
failure independent of SQLAlchemy so service-owned compensating storage cleanup
remains safe after ambiguous commits. Keep subscription snapshot assignment in
its repository and preserve the existing customer lock/commit lifetime. Clarify
CRUD, transaction and failure ownership in human/agent harness documentation only.
No schema, migration, Redis, external-provider or frontend changes are planned.
The subsequent router/service audit covers every v1 router, all services and
main/dependency request entry points; record remaining findings without silently
rewriting unrelated HTTP/auth interfaces.

# Verification Plan

Use make verify-plan then make verify with existing checks. Review error mapping,
rollback/compensation, reconciliation ordering/bounds and transaction lock scope.
Do not add new automated policy checks or tests per the user request.

# Impact

Internal ownership refactor; API payloads, codes, stored data and retry policies
remain compatible. Repository error translation must not hide ambiguous commits
or delete the currently committed photo.

# Loop Alignment

Request: Router -> Service -> Repository -> DB; preserve HTTP error conversion.
Events: existing API-key notifications remain after successful repository writes.
Background: reconciliation selects through the repository; worker ownership unchanged.
Frontend loops are not applicable: no frontend changes.

# Verification

- `make backend-format`: Ruff passed; existing photo failure mocks now use the
  repository error contract. No new test cases, assertions or policy checks.
- `make verify-plan` selected complete backend and governance scopes because auth
  DI/models and repository persistence changed; no scope downgrade was applied.
- `make verify`: passed in 61.3 seconds, including 504 backend tests, existing
  architecture fixtures/check, env/init checks and OpenAPI/consumer compatibility.
  Evidence: `.git/verification-logs/run-j1tmktqq/` (local).
- Existing test run emitted 18 warnings (dependency deprecations and coroutine
  resource warnings); no failing tests or new checker configuration.
- Manual source review found no session CRUD/transaction methods or SQLAlchemy
  imports in services/routers/auth DI; admin engine metadata remains intentionally.
- Frontend runtime/browser/build checks omitted because no frontend code, UI,
  consumer contract or gitlink changed. No DB schema changes; migration N/A.
- Router/service interface audit below records 8 remaining findings separately
  from the completed persistence refactor. No merge/deployment is requested.

# Router / Service Interface Audit

Reviewed 2026-10-27: all 8 v1 router modules (63 route handlers), all 12 service
modules (admin, api_key, auth, billing, billing_notifications,
billing_reconciliation, bootstrap, inbox, inquiry, notifications, profile_photo,
realtime), plus auth dependencies, main.py request handlers, all 6 domain error
modules, response builders and repository mutations used by those paths. This is
source review of the current checkout, not a new automated verification policy.
Redis implementation is excluded at the user's request.

## Fixed persistence findings

- billing_reconciliation: service opened get_db and executed scalars/select with
  predicates/order/limit. Selection now lives in BillingCustomers.
- APIKeyService: interpreted IntegrityError.orig/constraint strings. Repository
  maps the same duplicate/generic failure codes after rollback.
- AuthService: signup/OAuth creation caught IntegrityError, and directory listing
  caught SQLAlchemyError. UserRepository now owns those existing mappings.
- ProfilePhotoService: SQLAlchemy error catches coupled compensation to the driver.
  ProfilePhotos exposes PhotoPersistenceError; workflow compensation and existing
  public error codes remain service-owned. Existing failure mocks adopt this
  boundary; no test cases or assertions were added.
- BillingService: assigned attached ORM subscription fields. The repository now
  assigns snapshots inside the unchanged repository-owned locked context.
- deps.get_current_api_key: executed select, modified last_used_at/request_count,
  committed and refreshed. APIKeyRepository.record_valid_key_use now owns that
  operation; DI retains credential resolution and INVALID handling.

## Initial interface findings (superseded by worklog 0265)

This list records the original review, not the current outstanding-task list.
Worklog 0265 resolves config/inquiry/billing boundaries and enum/status/policy
consistency. The session-ID utility and AuthService Request suggestions were
withdrawn: they are allowed designs and do not require service/DTO wrappers.

1. **Service bypass in main.py /config.** The handler reads Users directly and
   calls create_access_token while composing bootstrap/profile configuration.
   Move the use case to a public configuration/bootstrap service, keeping response
   headers and response mapping in the handler. This is not a raw session write,
   but it bypasses the documented service entry point.
2. **Inquiry authorization decision in routers/v1/inquiry.py detail/reply.** Router
   computes user.role == UserRole.ADMIN and passes a trusted admin boolean.
   InquiryService also accepts booleans from list/detail/reply callers. Pass the
   authenticated actor/role and derive feature access inside service; keep coarse
   admin guards in deps. Repository ownership predicates remain transactional.
3. **Auth session construction in routers/v1/auth.py.** OAuth callback, token and
   login handlers call utils.token.create_refresh_session_id directly (3 sites).
   Expose a public service result containing session context and leave cookie
   rendering in the router. Cookie helpers, redirect construction and language
   header parsing themselves are legitimate transport operations.
4. **Transport parsing in AuthService.** login/oauth_callback_login accept Request
   and extract client IP/user agent; refresh_with_request_context reads cookies.
   Move parsing into a request adapter and pass explicit context/refresh inputs,
   while preserving forwarded-header precedence and JSON-versus-cookie behavior.
   This is interface coupling, not direct DB access or proof of an auth exploit.
5. **Private service API reuse in billing_notifications.py.** Calls another
   service's _known_prices once, _provider four times and _subscriptions once.
   Introduce purpose-specific public billing methods; do not just expose a raw
   provider client as the new public API. Preserve bounded calls/error mapping.
6. **Exception enum bypass in BillingService.** initialize and change_subscription
   compare .code.error to BILLING_PLAN_UNAVAILABLE / BILLING_CHANGE_CONFLICT string
   literals (2 sites). Compare to BillingErrorCode.<member>.code instead. All six
   domain exception modules otherwise use ServiceException/ErrorCode foundation;
   no raw HTTPException raises or JSON error responses were found in services.
7. **Result/policy duplication in auth routes.** Password-change/deletion-code
   services return None, while routers independently construct expires_in=600 and
   retry_after=30; those values are separately set when issuing challenges. Return
   policy/result metadata from the service. Current values match; this is a drift
   risk, not a currently observed TTL mismatch. Redis code remains out of scope.
8. **Literal HTTP status constants.** billing.create_card_setup uses status_code=201;
   auth.read_profile_photo declares a literal 200 response key. Replace with status
   constants to satisfy the existing decorator policy. main.health_ready likewise
   renders status_code=503, though this is an infrastructure response rather than
   a business error enum.

## Allowed paths and non-findings

- No direct DB-session CRUD/transaction calls remain in routers, services or deps.
  admin.get_engine only reads metadata. main lifecycle migration/engine operations
  and core health SELECT 1 are infrastructure responsibilities, not business CRUD.
- Routers' core imports are response/error builders, settings, logging and an
  ObjectStorage annotation/DI. No direct router mail/queue/storage/broker/provider
  business execution was found. Passing ObjectStorage via DI is not executing it.
- billing_webhook limits streamed HTTP body size and raises the existing billing
  enum on overflow; this is bounded transport validation, not subscription logic.
- OAuth callback catches map domain failures to documented redirects; refresh
  catches clear cookies then re-raise. These are documented transport exceptions.
- SSE passes through RealtimeService to core streaming, as explicitly documented.
  Its Request parameter supports disconnect handling; it is not DB access.
- notifications constructs an unpersisted outbox ORM record and passes it to a
  repository. No session method or attached-row assignment occurs in that service;
  replacing ORM result/input contracts with DTOs is a future coupling improvement.
- Startup/worker errors are not all HTTP domain errors: bootstrap ValueError and
  billing startup RuntimeError deliberately abort initialization. They are not
  missing endpoint error enums.
- No new automated checker, Make target or test case was added. Existing static
  architecture success does not prove these remaining interface issues absent.
