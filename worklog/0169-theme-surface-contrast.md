# Commit Title

fix(ui): improve contrast and share selection cards

# Changed File Scope

src/frontend gitlink and worklog/0169-theme-surface-contrast.md. Child owns shared CSS, SelectionCard, catalogue/locales, browser regressions and bilingual guides.

# Reason

Neutral/danger controls inherit the primary hover background while retaining incompatible text. Light category selection is weak, and sidebar/main surfaces are identical.

# Design

Keep shared controls and CSS ownership. Give neutral/danger actions their own hover colors; skip disabled hover styling. Use a selected category foreground/background pair, stronger light card boundaries, and a theme-specific sidebar surface consistent between expanded/collapsed modes. Use a shared sidebar CSS token; keep the studio preview scoped to the catalogue. Keep explicit and system dark declarations aligned. User additionally requested the category control as a shared selectable-card showcase: add controlled SelectionCard, reuse it in category navigation, and demonstrate selectable/disabled states.

# Verification Plan

Root frontend-format-check/frontend-test; child make check/test/build/test-ui/test-style-studio. Browser-computed text contrast at hover and surface distinction in light/dark, mobile/desktop; render screenshots for inspection. Stage and validate governance before each commit.

# Impact

Visual defaults and a reusable controlled SelectionCard; no API or navigation change. Sample selection stays local to the showcase. Existing studio overrides remain user-controlled.

# Loop Alignment

UI composition uses shared CSS and existing buttons. API state, realtime and desktop recovery logic are unchanged; no backend request/event/background work is needed for this visual change.

# Verification

Root make frontend-format-check and make frontend-test passed (85 tests). Child make check/test/build passed; make test-ui passed 60 cases and make test-style-studio passed 3 cases. Enabled hover text contrast >= 4.5:1 checked in explicit/system light/dark; screenshots inspected for light surfaces, dark modal cancel hover and mobile/desktop SelectionCard. No required checks skipped. B4React PR #25 merged as 1d83489c57aa55283d77f2e83bff4252626d5ae3 after Git governance and Frontend checks passed, including production routes and style-studio browser checks. Merged child tree is identical to the locally tested commit. Parent frontend contract comparison passed.
