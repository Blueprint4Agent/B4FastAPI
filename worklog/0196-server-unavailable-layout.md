# Commit Title

fix(frontend): integrate server unavailable sidebar layout

# Changed File Scope

src/frontend gitlink and this integration worklog.

# Reason

Deliver the simplified server-unavailable screen with the existing main sidebar.

# Design

B4React PR #48 merged as 5b63064d3ed18b0c3f263450948435cae0eecff1; pin this merge commit. Child owns source, tests and localized documentation.

# Verification Plan

Root make verify-plan and make verify, reusing unchanged successful child receipts; parent contract and packaging checks remain required.

# Impact

No backend/API/schema changes. Server recovery uses the app sidebar and one compact panel.

# Loop Alignment

UI composition follows existing AppLayout. Config retry and desktop recovery remain in existing owners; no new API or realtime behavior. Backend loops are not applicable to a frontend gitlink integration.

# Verification

`make verify-plan` selected frontend UI scope. Root `make verify` passed delegated checks and 119 unit/component/integration tests, 106 browser UI cases, OpenAPI contract alignment, production build and backend static packaging. Child PR #48 passed actual GitHub metadata validation and merged with a merge commit. Four mobile/desktop light/dark Korean recovery/showcase comparisons passed. Backend tests, production route recovery and style-studio browser suites were omitted by the UI classifier because no backend, routing, config or tooling changed. Local pre-push hooks remain enabled; actual parent PR metadata validation follows creation.
