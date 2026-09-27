# Commit Title

perf(frontend): integrate lazy page routes

# Changed File Scope

Pinned B4React revision and integration worklog.

# Reason

The startup bundle includes settings, admin and authentication screens even when the user only opens the showcase.

# Design

Module-level React.lazy for secondary pages; keep showcase and shared shell eager. Local Suspense preserves the sidebar and auth background. Route errors offer explicit reload or home navigation; no automatic reload loop. Keep auth guards intact. This task is separate from config sharing and state/memo harness changes.

# Verification Plan

Root frontend-format-check/frontend-test; child check/test/build/test-ui and production browser route loading/error tests. Compare built initial JavaScript with the 426.68 kB baseline. Staged governance and required CI.

# Impact

First secondary navigation loads a small extra chunk; deployed assets must retain compatible chunk files. CSS remains shared.

# Loop Alignment

API state and desktop recovery unchanged; no new realtime work. UI composition reuses PageStateFrame/Button; no new shared UI export or stylesheet.

# Verification

B4React PR #18 merged after Frontend checks and Git governance passed; MERGE method verified. Root make frontend-format-check frontend-test and make check test build passed (82 backend / 77 frontend tests); child test-ui passed 54 cases and test-routes passed 3 production cases. Entry JS reduced 426.68 to 390.76 kB (gzip 130.36 to 121.26). No required checks skipped.
