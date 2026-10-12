# Commit Title

feat(ui): refine inbox actions and inline profile editing

# Changed File Scope

Inbox table/selection/details/delete UI, profile count badge/order, shared checkbox variants, owner-scoped bulk APIs and deletion migration, contracts/tests/docs, and outside-click cancellation for profile inline edits, and support submission confirmation/role-specific follow-up labels.

# Reason

Replace the inline count and card list with a consistent collection UI, readable notification details and safe user-controlled deletion.

# Design

Place inbox directly after profile and display a compact trailing badge. Reuse admin table, shared buttons/checkbox and modal. Selection applies to the visible page; opening details marks read and only offers Close, per the final user request. Compact rows/buttons keep icon-label alignment. Filter changes retain the same-owner table while disabling stale actions until the new response. Bulk read/delete are owner-scoped and bounded. Deletion erases content and retains a tombstone/delivery key to suppress duplicate billing webhook replays. Post-commit SSE refreshes authoritative counts/lists.

# Verification Plan

Root make verify-plan/verify. Verify selection, partial selection, keyboard checkbox, detail/read behavior, confirm/cancel deletion, owner boundaries, tombstone deduplication and mobile/desktop light/dark geometry.

# Impact

Additive migration 0020 and API. Selected deletion is confirmed and cannot affect another user's records. No image build.

# Loop Alignment

Keep API hook state and account isolation; repository transaction precedes SSE invalidation. Existing desktop recovery remains. Profile cancellation discards only the local draft and does not submit an API request. Floating location menus remain part of the edit boundary; busy saves cannot be cancelled by outside clicks. No background task needed. Reuse collection/modal controls.

# Verification

Root make verify-plan and make verify selected backend plus full frontend verification (shared controls/styles). Backend 470 tests, frontend 168 tests, 211 browser checks, production route/style/contract/package/build checks passed. After the final outside-click change, focused inbox/profile browser coverage passed 26 tests, including save/country-region portal interactions and zero-write cancellation. Support requester/admin browser checks also passed 8 workflows. Child inbox/profile PR #79 merged at 3d7fc158412d296fa5d19abe7030736a837cf297. Support follow-up child PR #80 merged at 292196e772c25f496635048ba497570e0d0b6476; parent pins that merged commit. Final pre-push hooks revalidate the complete branch range. Migration 0020 applied to local PostgreSQL. No Docker/GHCR build or remote deployment: explicitly excluded by the user. No unrelated extra validation.
