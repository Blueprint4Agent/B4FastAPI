# Commit Title

fix(frontend): consolidate billing error feedback

# Changed File Scope

Frontend gitlink and integration worklog.

# Reason

Remove duplicate subscription/payment-details error banners and preserve compact Settings feedback.

# Design

Integrate child error composition and regression coverage after child PR merge. No backend or contract changes.

# Verification Plan

Child UI checks and parent Make-selected integration checks.

# Impact

Same errors and recovery, one deduplicated compact message; mutation error appears in active dialog.

# Loop Alignment

Existing API/recovery loops unchanged. Shared InlineMessage and Settings feedback reused. No new backend or realtime loop.

# Verification

Child PR #45 merged as 1e017b6e4dc7a35b2b75a724b259ea4033c3747e after UI verification (116 tests, 95 browser scenarios and build). Parent make verify-plan and make verify passed with frontend=ui/backend=False: matching check/test receipt reused, 95 browser scenarios passed in 59.7 seconds, frontend contract and packaging passed. No selected checks omitted. Backend/production route/style-studio checks were not selected for this presentation-only integration; full PR range is validated by pre-push.

Earlier browser runs were interrupted by repeated macOS sleep/dark-wake cycles and timed out. Resuming while awake passed without reducing scope or timeouts. Existing API/recovery loops and shared feedback composition are preserved; no new backend or realtime loop.
