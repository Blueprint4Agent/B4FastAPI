# Commit Title

perf(frontend): integrate React optimization harness

# Changed File Scope

Pinned B4React revision, root Make/CI integration, agent guidance and integration worklog.

# Reason

Make state ownership and React.memo optimization the default review workflow; prevent regression of shared config and lazy route gains. Evaluate Zustand/Redux against actual state needs.

# Design

Extract a memoized admin table with stable API items and locale-scoped date formatter. Keep filters/page API ownership in AdminPage. Add static guards for protected optimization boundaries, runtime render/production-route checks, and mandatory State Ownership/Memoization/Performance Evidence worklog sections for future runtime changes. Use the committed template as policy activation so historical commits remain valid. Do not add an external state library without a demonstrated shared-state need.

# Verification Plan

Child make check test build test-ui test-routes; root check/test/build and frontend-format-check/frontend-test. Harness rejection/acceptance fixtures and render work counts, plus PR CI.

# Impact

No API or persisted-state changes. Future runtime changes require an explicit state/memo decision and evidence; exceptions require reasons. CI runs production route recovery coverage.

# Loop Alignment

API state remains in page-owned hooks; no new realtime or desktop recovery owner. UI composition uses existing controls/classes with no shared UI catalog exports. Governance validates evidence, not performance correctness.

# State Ownership

Admin query/typing stays local, API snapshot belongs to useAdminUsers. Config/auth/connectivity remain scoped providers. Zustand deferred pending cross-screen high-frequency client state; Redux Toolkit deferred pending complex event/state workflows. No duplicated server cache or persisted credentials.

# Memoization

AdminUserTable is the default React.memo boundary: unchanged rows/loading/error props skip parent typing updates. Date formatter uses useMemo per language. No callback props/custom deep comparator. Context language changes must still rerender. Trivial controls and context owners are not blanket-memoized.

# Performance Evidence

Observed ten-row table: 20 initial date formats using one formatter; six draft-search keystrokes cause zero additional formats or formatter construction. Data/language/loading/error still update. Config sharing and route splitting remain protected; entry JS remains 390.76 kB (gzip 121.26). No elapsed-time improvement is claimed.

# Verification

B4React PR #19 merged after required Git governance and Frontend checks passed, including Chromium production-route cases; MERGE method confirmed and merged source matches tested commit. Root make check test build passed (82 backend / 79 frontend tests, including frontend-format-check/frontend-test). Child make test-ui: 54 passed; root frontend-test-routes: 3 passed. Root frontend-react-performance-check passed: 6 static fixtures and 10 governance tests, including real index/committed-snapshot isolation. No required checks skipped; backend domain/event/task loops are not applicable because only frontend/workflow integration changed.
