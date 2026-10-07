# Commit Title

fix(frontend): integrate billing and admin loading surfaces

# Changed File Scope

Frontend gitlink and integration worklog.

# Reason

Contain billing failures within their cards and replace administrator loading text with spinners.

# Design

Integrate the merged child UI change using existing settings surfaces and shared status components.

# Verification Plan

Run root make verify-plan and make verify after child merge; reuse unchanged child checks where the harness permits.

# Impact

UI-only; no API, migration or backend logic change.

# Loop Alignment

Existing frontend API state and retry owners unchanged; UI composition follows settings/admin families. No backend or realtime loop changes.

# Verification

Child PR Blueprint4Agent/B4React#61 merged. Child and root make verify-plan / make verify passed frontend=ui: 140 tests, 164 browser checks, contracts and packaging/build. Backend and full-only suites were omitted by the classifier because the changes are UI-only. Existing Billing/General comparisons and admin memoization tests passed.
