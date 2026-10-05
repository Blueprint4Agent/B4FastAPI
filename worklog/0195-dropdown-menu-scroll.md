# Commit Title

fix(frontend): integrate floating dropdown scroll recovery

# Frontend Integration

B4React PR #47 merged with merge commit `258bfa44a178430f70dfd1ddc24cd8f79e559bbb` after actual PR metadata and local UI push checks passed.

# Changed File Scope

Verified B4React gitlink and integration worklog.

# Reason

Country/region list scrolling resets in the new billing editor; integrate the shared dropdown correction into the same parent task PR.

# Design

Child owns wheel/resize placement correction and browser regression. Merge its fix PR before updating the parent pin; retain API contract and packaging validation.

# Verification Plan

Child Make-selected UI checks and country-wheel regressions, then root verify-plan/verify integration checks.

# Impact

Long floating menus scroll to their last option without resetting; billing APIs unchanged.

# Loop Alignment

Shared UI scroll/placement loop corrected; request, realtime and connectivity loops unchanged. No backend/background work applies.

# Verification

Child `make verify-plan` selected UI scope; checks and 119 tests, 106 browser cases and build passed. Before correction the country wheel test reproduced scrollTop=0; four mobile/desktop light/dark wheel/resize/final-selection cases now pass. Root `VERIFY_BASE=39504cd440d266411dde61167980e41612b4794b make verify-plan` selected the full branch scope; matching `make verify` passed all selected checks, 227 backend tests, 119 frontend tests, 106 UI cases, production routes, style studio, contracts/package and project-build isolation. No selected root checks omitted. Child production-route/style-editor checks were omitted by its UI-only plan and are covered by root integration. Native desktop bundling is outside the browser billing change.
