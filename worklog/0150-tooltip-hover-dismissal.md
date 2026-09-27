# Commit Title

fix(frontend): adopt tooltip hover dismissal fix

# Changed File Scope

src/frontend gitlink and worklog/0150-tooltip-hover-dismissal.md.

# Reason

Tooltips remain visible after hovering a previously clicked, still-focused button.

# Design

Adopt the merged B4React fix separating keyboard-visible focus from pointer focus,
with window-blur dismissal and browser regressions. No layout or API changes.

# Verification Plan

Root make frontend-format-check/frontend-test and contract-check. Child make
check/test/build and test-ui. Require passing governance/code CI and merge commits.

# Impact

Pointer tooltips close on leave while keyboard descriptions remain accessible.

# Loop Alignment

UI composition uses shared Tooltip; no API state, realtime, desktop recovery, or
backend request/event/task loop changes, so those loops are not applicable.

# Verification

- Child PR #5 passed Git governance/Frontend checks and merged as
  75e359aa3933893678f8bcd7dc58b03b75350d1a; auto-merge verified as MERGE.
- Root frontend-format-check/frontend-test (51 tests) and contract-check passed.
- Child make check/test/build passed; make test-ui passed all 8 browser cases.
- Two new regressions failed before the fix and passed afterward: pointer click,
  re-hover, leave; keyboard focus, pointer leave, window blur.
- Native desktop was not launched; this change only affects browser DOM events.
