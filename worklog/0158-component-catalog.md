# Commit Title

refactor(frontend): adopt audited component catalog

# Changed File Scope

Shared UI and OAuth components, showcase composition/styles/locales, audit docs and tests. Parent owns the frontend pin.

# Reason

Showcase examples omit live components and contain obsolete wrappers, duplicate provider logos and hard-coded labels.

# Design

Audit imports and showcase coverage. Remove unused ThemeToggle wrapper and obsolete OAuthOptionsCard; preserve the requested ThemeToggleButton demo. Retain useful MenuList/KeyValueCard with compact tokens. Share OAuth logo rendering. Add local-state previews for live upload/copy/avatar/provider/API-key components. Organize localized catalog with category navigation, search and empty/reset states. Use shared components without real API actions.

Extend the TypeScript-aware harness to reject missing rendered UI exports,
inline appearance, isolated stylesheets and copied shared button styling. Test
checker failures with fixtures; run via architecture-check in child and parent CI.

Loading and 404 pages reuse PageStateFrame/PanelCard, localized compact chrome,
shared actions and accessible loading status; preview loading has an exit action.

# Verification Plan

Child make check/test/build/test-ui; root frontend-format-check/frontend-test. Verify filters, sample interactions, mobile overflow and light/dark layouts. Record retained showcase-only components and component coverage.

# Impact

No auth/API contracts change. Catalog previews are isolated from account data. Public exports drop unused ThemeToggle.

# Loop Alignment

UI composition through shared controls and actual feature components. API, realtime and desktop loops unchanged; previews use local state only.

# Verification

Child make check/test/build/test-ui passed: 62 Vitest cases, 43 browser cases,
and seven harness fixtures. Root frontend-format-check/frontend-test/frontend-architecture-check passed.
Reviewed actual /loading and unknown-route 404 at 390/1440px, and light/dark catalog/search screenshots.
No backend/API/realtime changes; local previews do not invoke account mutations.
Removed ThemeToggle wrapper/OAuthOptionsCard; retained useful MenuList/KeyValueCard
and showcase-only ThemeToggleButton. Audit docs list the shared components and runtime consumers.
