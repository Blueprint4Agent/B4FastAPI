# Commit Title

style(frontend): adopt compact profile navigation

# Changed File Scope

src/frontend gitlink and this worklog.

# Reason

Adopt a more compact sidebar and a reference-inspired profile popup containing
only existing actions, with settings consolidated in the profile menu.

# Design

Merge the child PR, then pin its merge commit. Child owns markup/styles/tests and
bilingual documentation. No parent API or packaging changes.

# Verification Plan

Run frontend-format-check/frontend-test and confirm child check/test/build/test-ui.
Validate staged governance and wait for required CI before merge.

# Impact

Sidebar widths are 48px/176px; profile popup groups avatar/identity, settings/theme,
and conditional logout. Existing touch sizing and dismissal behavior remain.

# Loop Alignment

Shared UI composition is preserved. API/realtime/desktop recovery unchanged;
backend lifecycle/event/task loops are not applicable to this presentation pin.

# Verification

B4React PR #8 merged as 72773193fc7aae0ca5efa1d5abd41ae7c6517632 after
required checks passed, with MERGE auto-merge method verified. Root
frontend-format-check/frontend-test passed against the merged pin (52 tests).
Child check/test/build/test-ui passed (16 browser cases), and light/dark
mobile/desktop screenshots were reviewed. No required checks skipped.
