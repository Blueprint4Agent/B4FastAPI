# Commit Title

feat(frontend): integrate landing section navigation

# Changed File Scope

Pinned B4React gitlink, bilingual frontend integration notes and this worklog.

# Reason

Refine the landing from the supplied references: persistent capsule section navigation, image-only preview framing, top icon-pill source links, feature cards, development steps, use cases and a grouped footer. Remove home-only coffee support.

# Design

Keep the selected service shell and theme tokens. Use native section anchors with smooth scrolling and reduced-motion fallback, centered in the topnav/minimal header as plain links; sidebar retains a capsule. Use target offsets, full-width footer and six-second image crossfades with progress. Hover/focus do not pause; explicit pause, enlargement, reduced motion and offscreen/hidden states do. Keep actual auth-gated destinations and demo previews. Use real repository/guide links; no invented legal pages, metrics or customer claims. Development steps reflect clone/configure, build features, verify/deploy; use cases describe possible applications rather than deployed customers.

# Verification Plan

Run make verify-plan and make verify. Browser-check sticky navigation and target visibility across three layouts, mobile/desktop, light/dark and reduced motion. Check keyboard links, preview modal, footer permissions and unchanged static introduction.

# Impact

Home composition changes only. Global coffee links remain development-only. No new API, dependencies, data persistence or deployment variables.

# Loop Alignment

UI composition uses existing tokens and Button/Modal. API, realtime and desktop recovery owners remain unchanged; no new request/event/background loops are needed.

# Verification

B4React PR #88 merged as ff1eb6556c3c6bc142df2751ec87f877e1e55311. Root make verify-plan selected full frontend integration. make verify passed hook fixtures, branding, contract/package checks (0.1s) and project build tests (12.8s); it reused matching child check, 195 unit/component tests, 240 browser cases, 10 production route cases, 11 discovery cases and 3 Style Studio cases. No selected checks were omitted. Backend runtime tests are not applicable to a frontend gitlink/docs-only integration. Manual browser measurements confirmed centered minimal header text, decoded images, overlapping crossfade opacity and progressing gauge while hovered. Image publication is deferred while the user selects deployment layout configuration.
