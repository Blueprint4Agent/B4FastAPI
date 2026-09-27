# Commit Title

feat(frontend): adopt robot brand identity

# Changed File Scope

Brand assets, shared BrandMark/banner, application usage, showcase, guides and tests; parent owns frontend pin.

# Reason

Replace the text tile with the supplied robot-inspired identity in light/dark, rounded-square and horizontal B4A forms.

# Design

Create crisp native SVG silhouettes with antenna, ear disc and rounded visor. Reuse one shared mark with adaptive palette and tile/plain variants; compose accessible B4A wordmark banner. Preserve expanded sidebar text-only header. Register every variant in showcase and use adaptive favicon.

# Verification Plan

Run child check/test/build/test-ui and root frontend-format-check/frontend-test. Inspect light/dark desktop/mobile and small icon geometry.

# Impact

Visual identity only; no auth, API or persistence changes.

# Loop Alignment

Shared component/showcase composition followed. API, realtime and desktop recovery loops not applicable to static branding.

# Verification

Child make check/test/build/test-ui passed: 62 tests and 39 browser cases.
Root frontend-format-check/frontend-test passed. Reviewed both palettes, corrected
goggle-to-head spacing, mobile overflow and RGBA PNG exports (512px icons, 1024×320 banners).
No API/realtime/desktop recovery changes; those loops are not applicable.
