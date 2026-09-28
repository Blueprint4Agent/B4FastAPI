# Commit Title

fix(ui): use formal Korean toast messages

# Changed File Scope

src/frontend gitlink and this integration worklog; Korean toast/showcase copy and bilingual guidance belong to B4React PR #27.

# Reason

The user requested formal Korean endings such as 했습니다 instead of 했어요.

# Design

Keep the existing capsule and action dispatch behavior; revise only Korean display copy, including the showcase sample.

# Verification Plan

Child make check test build; root make frontend-format-check frontend-test. Inspect all toast strings for informal endings. No new tests needed for copy-only changes.

# Impact

Display text only; no API, state, timing or layout rule changes.

# Loop Alignment

UI composition continues using the existing ToastCard. API/realtime/desktop/backend loops are unchanged and not applicable to localized copy.

# Verification

Child make check test build and parent make frontend-format-check frontend-test passed (93 tests). Reviewed all 21 Korean action messages and the showcase sample; no 했어요/없어요 endings remain. No new tests or repeated browser layout run for copy-only edits; the unchanged capsule layout passed 65 browser cases in the preceding implementation. B4React PR #27 merged as f4e24b501023e8e46e330821a51ca5b11a94e529 after Git governance and Frontend checks passed. MERGE registration verified; parent required CI remains mandatory.
