# Commit Title

feat(frontend): adopt native shortcuts and compact dropdowns

# Changed File Scope

Pinned src/frontend gitlink and this worklog.

# Reason

Adopt shared OS-aware shortcut hints/actions and compact trigger-aligned dropdowns.

# Design

Integrate the merged B4React change through its pinned gitlink after child CI.
No parent runtime or API contract changes.

# Verification Plan

Run root frontend-format-check and frontend-test; confirm child checks and merge.

# Impact

Mod+B toggles the sidebar and Mod+, opens settings outside editable/modal contexts.
Dropdowns share trigger width, 4px gap, compact 32px desktop and 44px touch targets.

# Loop Alignment

UI composition is verified in B4React through shared primitives and browser tests.
API state, realtime and desktop recovery loops are unchanged: no transport changes.
Backend loops are not applicable to this frontend pin update.

# Verification

Root frontend-format-check/frontend-test passed with 55 tests against child source.
Child check/test/build and 26 browser cases passed. B4React PR #10 merged as 674a4325 after required CI passed.
Parent CI runs on the integration PR.
