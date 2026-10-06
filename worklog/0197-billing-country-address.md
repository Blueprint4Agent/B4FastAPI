# Commit Title

fix(frontend): integrate billing address and action refinements

# Changed File Scope

src/frontend gitlink and integration worklog.

# Reason

Billing profile editing needs country-specific regional choices. Follow-up UI requests group error/retry and attach lightweight text actions to their sections, with showcase examples.

# Design

B4React PR #49 merged as acbd0334314b197f290245cfed801231f2d0dff0; pin this merge commit. Stripe AddressElement validates address completeness; the existing profile API and backend remain unchanged. The child also owns the shared text Button, StatusCard action, billing placement and showcase.

# Verification Plan

Root make verify-plan / make verify, matching the Git hook environment for valid child receipt reuse. Contract alignment and packaging remain mandatory.

# Impact

Configured Stripe installations receive country-specific address fields. Manual fallback stays available when no public key is configured. No migrations or new dependencies.

# Loop Alignment

Existing page-owned profile mutation and connectivity recovery stay intact. UI composition reuses the compact modal and host tokens. No new realtime events or backend lifecycle changes.

# Verification

Root make verify-plan selected frontend UI scope. Root make verify passed 122 unit/component/integration tests, 112 browser cases, contract alignment, production build and static packaging. Child PR #49 passed actual metadata validation and merged with a merge commit. Backend tests, production route recovery and style-studio browser suites were omitted by the classifier because no backend/routing/configuration changes were made. Live provider fields were exercised for KR/US/JP at mobile/desktop widths in light/dark with synthetic addresses; profile saves were intercepted, so no real customer was changed. Local governance/hooks remain enabled.
