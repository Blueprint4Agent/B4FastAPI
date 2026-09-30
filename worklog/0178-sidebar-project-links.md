# Commit Title

feat(frontend): integrate sidebar project links

# Changed File Scope

Pinned B4React frontend revision and this integration worklog.

# Reason

Expose GitHub and the user guide immediately above the sidebar profile control.

# Design

Integrate the merged B4React task PR. Links use existing sidebar rows/tooltips, the official GitHub SVG, and localized User guide / 사용 가이드 labels. Documentation targets https://blueprint4agent.github.io/docs.

# Verification Plan

Run root make verify-plan and make verify; reuse completed child checks as documented by the verification policy, and run remaining parent contract/package/custom-branding integration checks. Validate staged Git/PR metadata.

# Impact

Static external links only; no backend contract or database changes.

# Loop Alignment

UI composition reuses existing shared sidebar and Tooltip. API state, realtime, desktop recovery, backend request/event/background loops are not applicable because static links add no server or async state.

# Verification

Root make verify-plan selected full frontend scope and no backend scope. Child make verify passed check/test (97), UI (71), production routes/build (6) and style-studio (3); reused this unchanged-content evidence rather than repeating the delegated checks. Root make verify-light frontend-contract-check frontend-package-verified project-build-test passed, including six production checks against isolated custom branding. The full root runner would repeat the already successful child targets, so executed its remaining root Make targets per the no-repeat policy. Backend checks omitted because only the frontend pin changes. Visual review confirmed desktop dark/mobile light layout and Korean 사용 가이드 label. GitHub and guide links are above profile; guide returned HTTP 200. Child PR: https://github.com/Blueprint4Agent/B4React/pull/31; Git governance and Frontend checks passed, merged via merge commit 68c4955d4c2a8a72db76912fe60265c9a629b1c1. The merged tree matches tested child commit 3833286.
