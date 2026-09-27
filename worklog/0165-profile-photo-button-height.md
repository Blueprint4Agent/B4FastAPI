# Commit Title

fix(frontend): integrate matching photo action heights

# Changed File Scope

Pinned B4React revision and integration worklog.

# Reason

Choose photo uses a label with only a minimum height while Remove photo uses Button with a fixed control height, producing unequal profile actions.

# Design

Use the shared control-height token for both avatar upload actions; retain the coarse-pointer minimum target. Preserve file selection/removal behavior and existing shared UI composition.

# Verification Plan

Measure actual browser geometry before/after at desktop/mobile and coarse-pointer widths in English/Korean. Run root frontend-format-check/frontend-test, child check/test/build/test-ui, and integration checks. No new tests for this small reversible CSS change.

# Impact

Photo actions have matching height; no API, state or persistence changes.

# Loop Alignment

UI composition uses the shared avatar control and app.css. API/realtime/desktop recovery loops unchanged; backend loops not applicable to CSS.

# State Ownership

Not applicable: CSS geometry only, existing page/hook ownership unchanged.

# Memoization

Not applicable: no render or state logic change; no new memo boundary needed.

# Performance Evidence

Chromium production-build measurements in EN/KO at 1440px and 390px fine-pointer viewports: before 32px selection / 36px removal; after both 36px. At 390px coarse-pointer both remain 44px. Screenshots visually reviewed. No rendering speed claim.

# Verification

B4React PR #20 merged as 999f283 after required Frontend checks and Git governance passed (MERGE method verified). Merged source matches the tested change. Root frontend-format-check/frontend-test and make check test build passed (82 backend / 79 frontend tests); child test-ui passed 54 cases. Six before/after browser variants and screenshots confirm geometry. Required child CI also passed production-route tests. No new tests for this small reversible CSS correction; no required checks skipped.
