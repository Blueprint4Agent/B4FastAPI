# Commit Title

feat(frontend): adopt compact settings and API key management

# Changed File Scope

src/frontend pinned gitlink and this integration worklog.

# Reason

Adopt the shared resizable sidebar, modern compact settings/profile/API-key UI,
preview theme selection, lighter typography and quieter borders.

# Design

Merge B4React PR #9 first and pin its merge commit. Child owns shared/sidebar
layout, settings query navigation, preview selector, table/modal presentation,
legacy toggle placement, typography, tests and bilingual guides. Parent owns only
the integration pin; no backend or API contract changes.

# Verification Plan

Run root frontend-format-check/frontend-test/contract-check after the final pin.
Confirm child check/test/build/test-ui and required CI; validate staged governance.

# Impact

Settings shares the app sidebar, header and footer. Expanded width defaults to
224px, resizes 200–360px and persists. Profile popup follows sidebar width. Profile
and API-key content is compact; legacy theme toggles remain showcase-only. Existing
API-key mutation, realtime, secret reveal and offline protections are preserved.

# Loop Alignment

Shared UI composition and page-owned domain hooks are retained. API/realtime and
desktop recovery loops are unchanged. Backend lifecycle/event/task loops are not
applicable to this frontend integration pin.

# Verification

B4React PR #9 merged as afda187b7f1eceb31e3b62ff6a2a44cf695b2d91 after
Frontend checks and Git governance passed; auto-merge method verified as MERGE.
Root make frontend-format-check/frontend-test/contract-check passed against the
merged pin (52 tests, matching provider/consumer OpenAPI). Child check/test/build
passed; test-ui passed 21 browser cases. Light/dark mobile/desktop screenshots
reviewed for settings, profile, API table and creation dialog. No required checks
skipped.
