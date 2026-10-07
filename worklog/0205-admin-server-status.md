# Commit Title

feat(admin): expose server and effective environment status

# Changed File Scope

Admin status API, health probes, tests, contracts, admin UI and localized documentation.

# Reason

Show actual dependency health and safe effective feature modes in a consistent administrator screen.

# Design

Admin-only read API delegates to a service and bounded concurrent readiness probes. SMTP authentication without email and one Stripe Checkout list read use a per-process 60-second cache and single-flight tasks; API responses wait at most five seconds. Startup evidence is retained separately. Return only safe feature flags plus database/Redis hostname and port, never credentials, database names or options. CodeBadge is shared and showcased for variable names, allowlisted raw values and addresses. The UI reuses the settings/home shell and a full-width PanelCard with aligned values; OAuth icons sit beside the label without a health badge.

# Verification Plan

Run make verify-plan then make verify; exercise authorization, timeout, safe flags, stale recovery and desktop/mobile light/dark peer comparison.

# Impact

Read-only operational visibility. No migrations or feature configuration writes.

# Loop Alignment

Backend request/service/model/error and observation boundaries are followed. No mutation events or Celery jobs apply to read-only probes; ephemeral in-flight network tasks are shared and cleaned up at lifespan shutdown. Frontend uses owner-scoped requests, cancellation, 30-second visible-page polling, focus/network/desktop recovery and stale results after failures or 60 seconds. No domain SSE event exists for external connection changes.

# Verification

Root `make verify-plan` selected backend=True and frontend=full; `make verify` passed. Backend: 253 tests. Frontend: 128 tests, 151 browser UI tests, 9 production route tests and 3 Style Studio browser tests. Architecture, hooks, env/contracts, packaging and project-build checks passed. No selected checks were omitted. Final targeted column comparisons also passed at 390/1440px light/dark. Live read-only smoke reported server/database/cache/email/billing healthy without delivering email or creating a billing resource.

An intermediate parallel browser run lost its shared Vite server; it was discarded and verification was rerun sequentially. A showcase test URL typo was corrected to /show-case before the passing run. No hook was bypassed.


Frontend integration: B4React PR #56 merged as `3b429637989494a1d716482ecf8095b42676ade2` before updating the parent gitlink. Root and child use merge commits. Issue #93 remains outside this change. The generated untracked SQLite artifact was preserved outside the checkout and excluded from commits.
