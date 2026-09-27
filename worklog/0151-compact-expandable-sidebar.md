# Commit Title

refactor(frontend): adopt compact expandable sidebar

# Changed File Scope

src/frontend pinned B4React gitlink and worklog/0151.

# Reason

Adopt the requested compact sidebar shell, brand-based expansion, compact tooltips,
and consistent animated open/close states from B4React.

# Design

Merge the B4React sidebar PR first, then pin its merge commit. The child owns all
layout, styling, locale, test, and bilingual documentation changes. Parent packaging
and API contracts remain unchanged.

# Verification Plan

Run root make frontend-format-check, frontend-test, contract-check. Confirm child
make check/test/build/test-ui and required PR CI. Validate staged Git governance.

# Impact

App navbar is replaced by a 56px collapsed / 200px expanded sidebar with footer
profile controls. Brand hover reveals expansion, expanded header closes from the
right, and 180ms width transitions preserve the same theme surface. Touch sizing,
reduced motion, compact tooltips, and menu spacing are covered in the child.

# Loop Alignment

UI composition uses shared AppLayout/Sidebar and common controls. Desktop recovery
preserves retry/offline logout guards. API/realtime behavior remains unchanged.
Backend lifecycle/event/task loops are not applicable to this frontend pin update.

# Verification

B4React PR #6 merged as cef309a888e9a176ff2ddf45b8c989b67d1f0b47 after
Frontend checks and Git governance passed; registered auto-merge method was MERGE.
Root `make frontend-format-check frontend-test contract-check` passed against the
merged pin (52 tests and matching OpenAPI contracts). Child `make check test build
test-ui` passed with 52 unit/component/integration tests and 16 Chromium cases.
Mobile/desktop light/dark screenshots reviewed. No required checks skipped.
