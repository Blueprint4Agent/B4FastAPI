# Commit Title

refactor(backend): align service interfaces and policy constants

# Changed File Scope

Backend bootstrap/config, inquiry and billing service boundaries; auth policy/status
constants; AGENTS and English/Korean backend harness guidance; audit reconciliation.
Keep follow-up work in the existing task branch and PR #160.

# Reason

Resolve confirmed business orchestration/authorization/private-interface issues and
small enum/status/policy consistency gaps without treating every utility call or
HTTP Request dependency as a violation.

# Design

Move config/profile/token orchestration into the existing BootstrapService.
Move inquiry actor-role interpretation into InquiryService, preserving admin DI and
repository ownership filters. Billing exposes notification use cases returning
plain results instead of leaking its private provider client; reuse pure price
parsing as a utility. Share email-code lifetime/cooldown constants without changing
Redis mechanics. Use existing error enums and HTTP status constants.
Document required boundaries separately from consistency conventions and allowed
utilities/Request usage. No new automatic check, test case, schema or API contract.

# Verification Plan

Run make backend-format, then make verify-plan / make verify through existing
checks. Review bootstrap fresh tokens, inquiry owner/admin/manager visibility,
notification ownership/current-provider-state/pending-update behavior, and identical
challenge lifetimes/error/HTTP contracts. Update the existing ready PR metadata.

# Impact

Internal refactor with unchanged HTTP payloads, role behavior, Redis, SQL schema,
provider timeout/error mapping and frontend contracts. Do not add services merely
to wrap technical helpers or replace working Request adapters with DTOs.

# Loop Alignment

Request: config/inquiry/billing business work goes through service entry points.
Events: inquiry inbox publication and billing event handling remain after the same
successful operations. Background notification delivery/reconciliation unchanged.
Frontend loops N/A: no frontend implementation or gitlink change.

# Verification

- `make backend-format`: Ruff lint/format passed.
- `make verify-plan` selected complete backend and governance checks because auth,
  main/config and shared service inputs changed; no manual scope downgrade.
- Final `make verify`: passed in 57.9 seconds. Existing backend suite: 504 passed,
  18 warnings. Existing architecture (104 app files), initialization/environment,
  governance harness and provider/consumer OpenAPI compatibility checks passed.
  Local evidence: `.git/verification-logs/run-ilcmgvea/`.
- Existing coverage includes fresh bootstrap tokens/profile refresh, inquiry
  owner/admin/manager visibility, stale-event rejection, subscription reconciliation
  and billing notification/error behavior. No tests/checkers/Make targets added or
  modified in this follow-up; Redis implementation is untouched.
- Manual review confirmed no cross-service private billing calls or duplicated
  domain error/status literals in the affected request/service paths; router session
  ID helpers and AuthService Request adapters remain unchanged.
- Frontend runtime/UI/browser/build checks omitted because no frontend, UI,
  consumer contract or gitlink change. Schema migration N/A: no schema change.
- Original persistence refactor in 0264 remains covered in the same task PR; no
  merge or deployment requested.

# Resolution of Initial Audit

- Required boundaries: config orchestration uses existing BootstrapService;
  inquiry detail/reply derive privileged access in InquiryService; notification
  provider validation uses public BillingService operations returning plan/boolean/
  language results, never a raw SDK client.
- Consistency: domain enum comparisons, named HTTP status constants and shared
  account-code TTL/cooldown constants. Redis implementation remains untouched.
- Allowed existing design: random session-ID/cookie utilities called by routers,
  and AuthService Request inputs. No forwarding service, Request DTO or new
  automatic checker/test is introduced for these uses.
- Initial audit in 0264 is marked superseded so it is not interpreted as eight
  still-outstanding violations.
