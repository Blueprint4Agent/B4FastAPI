# Commit Title

perf(frontend): integrate shared app configuration

# Changed File Scope

Pinned B4React revision and integration worklog

# Reason

Share /config between app, authentication, sidebar and pages; initial production navigation currently makes 3–4 identical requests.

# Design

Provider-scoped state and in-flight promise deduplication. Stable ensureConfig reads the current snapshot; reload explicitly refetches. One desktop recovery coordinator reloads configuration before session revalidation. Keep failed configuration distinct from disabled login and retry through the same owner. No code-splitting or memo changes in this task.

# Verification Plan

Root frontend-format-check/frontend-test; child check/test/build/test-ui; parent integration check/test/build; production request-count measurement and staged governance.

# Impact

No public API or configuration schema changes; no persistent caching of bootstrap tokens. Providers are scoped to the mounted application.

# Loop Alignment

API state centralized; desktop recovery refreshes config then session. Realtime and UI composition unchanged. No backend or mutation loops apply.

# Verification

B4React PR #17 merged as 77de190 after Frontend checks and Git governance passed (MERGE method). Root make frontend-format-check frontend-test and make check test build passed (82 backend / 77 frontend tests). Child make test-ui passed 54 browser tests; config is requested once on initial showcase/settings/admin and one additional time on explicit failure retry. No required checks skipped.
