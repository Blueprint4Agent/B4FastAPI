# Commit Title

feat(frontend): integrate prompt builder discovery

# Changed File Scope

src/frontend gitlink, notes/search-discovery.md, notes/ko/search-discovery.md and worklog/0254-prompt-builder-discovery.md.

# Reason

Make the existing prompt builder discoverable from Home and About with a concise introduction and direct entry.

# Design

Reuse the home overview section heading, workflow region and resource-pill actions. Add a primary home hero link, a compact introduction before capabilities, and a footer entry. Static English/Korean About renders the same localized introduction and CTA without requiring JavaScript, preserving prefixed app URLs and opt-in discovery. No wizard logic or backend changes.

# Verification Plan

Run make verify-plan then make verify. Extend existing discovery coverage to check static/prefixed links, production guest navigation to the wizard and shared section/action geometry at 390/1440 light/dark in both languages. Inspect screenshots. Validate child/parent metadata and child-first integration.

# Impact

Adds public entry points to an existing guest-accessible route. No persistence, API, dependency or permission changes. Existing discovery opt-in and app readiness gates remain authoritative.

# Loop Alignment

UI composition applies through existing home classes and navigation. API state, realtime, desktop recovery and backend request/event/task loops are not applicable: only static copy and links change.

# Verification

B4React PR #92 merged at 3caa104d49f5e09138a53c4b9a0960839e2927e9 (source 2fb4185). Child verify-plan selected full frontend and make verify/pre-push passed: check, 209 unit/component/integration tests, 250 UI cases, 15 production routes, 11 discovery cases and style-studio. Observed bilingual mobile/desktop light/dark link navigation, shared pill/heading styles and no overflow; static/prefixed links verified. Child actual PR metadata validated before merge. Root make verify-plan selected backend=False/frontend=full. Root make verify passed hooks-test, project-brand, frontend-contract-check frontend-package-verified and project-build-test; matching child check/test/UI/routes/style receipts were reused. Backend suite omitted locally because only the frontend pin and documentation changed.
