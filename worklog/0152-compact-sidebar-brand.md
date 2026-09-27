# Commit Title

style(frontend): adopt compact text-branded sidebar

# Changed File Scope

src/frontend gitlink and this integration worklog.

# Reason

Adopt a smaller sidebar and a text-only B4A brand aligned with menu icons, without
expanded-brand hover fill.

# Design

Merge the child change first and pin its merge commit. The child owns CSS tokens,
brand markup/locales, layout test dimensions and bilingual guide changes.

# Verification Plan

Run root frontend-format-check/frontend-test and confirm child check/test/build/test-ui.
Wait for required CI and validate Git governance metadata before merging.

# Impact

Desktop rail/panel widths become 52px/184px with 32px icon controls and 36px rows.
Brand/menu horizontal padding is 12px. Touch targets retain 44px dimensions.

# Loop Alignment

UI composition reuses shared sidebar/global CSS. API state, realtime and desktop
recovery are unchanged. Backend loops are not applicable to this frontend pin.

# Verification

B4React PR #7 merged as 9722df1473a06b1d042dfb4944e1a3a5f800eafa after
required checks passed; auto-merge method verified as MERGE. Root
frontend-format-check/frontend-test passed against the merged pin (52 tests).
Child check/test/build/test-ui passed (16 browser cases); light/dark mobile and
desktop screenshots reviewed. No required checks skipped.
