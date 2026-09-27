# Commit Title

fix(frontend): adopt refined components and tooltip placement

# Changed File Scope

- src/frontend (pinned B4React submodule)
- worklog/0149-refine-frontend-components.md

# Reason

Adopt consistent component padding, radii, typography, and cleaner navigation while
preserving existing branding. Fix tooltips anchored to stretched wrappers and
use black-on-light / white-on-dark tooltip surfaces.

# Design

Integrate the merged B4React UI change after its governance and frontend CI pass.
The child owns shared styling, tooltip body-portal positioning with viewport
collision/scroll updates, browser regressions, and English/Korean documentation.
No backend contract or runtime policy changes.

# Verification Plan

Run root make frontend-format-check, make frontend-test, and make contract-check.
Verify the child merge commit is pinned and both PRs pass required CI and use merge
commits. Child make check/test/build and test-ui cover component geometry.

# Impact

Shared visual refresh; mobile sidebar expands over content. Tooltip placement and
inverse theme colors are corrected. No new dependencies or API schema changes.

# Loop Alignment

UI composition uses existing shared components and app.css, verified at mobile and
desktop widths. API state, realtime refresh, desktop recovery, backend request,
domain event, and task loops are not applicable: no data or lifecycle changes.

# Verification

- B4React PR #4 merged as 1768f8576d1d4894cfec4326ce81185fb9021510 after
  Git governance and Frontend checks passed. Auto-merge method verified as MERGE.
- Root make frontend-format-check, make frontend-test (51 tests), and make
  contract-check passed against the adopted frontend tree.
- Child make check/test/build passed; make test-ui passed 6 Chromium cases.
- Inspected light/dark showcase and login at mobile/desktop widths. Native Tauri
  launch was not run; desktop component coverage passes and titlebar insets remain.

Local CORS report was diagnosed
as a separate Observability Lab service bound to 127.0.0.1:8000, returning /config
404 without CORS headers. The B4FastAPI allowlist already includes localhost:5173
and 127.0.0.1:5173; no CORS policy change is needed.
