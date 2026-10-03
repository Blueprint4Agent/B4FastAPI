# Commit Title

fix(frontend): align billing actions and provider marks

# Changed File Scope

Frontend gitlink and integration worklog.

# Reason

Match subscription cancellation with the existing account-deletion UI and identify Link/Stripe with official artwork.

# Design

Integrate child branding and Settings-family alignment after its PR merges. Keep provider-owned card details, Link wallet lookup and all billing APIs unchanged.

# Verification Plan

Root Make verification plan and selected integration checks, child browser evidence and governance.

# Impact

Presentation and external wallet lookup only. No backend contract, migration or payment mutation behavior changes.

# Loop Alignment

Existing API loading/focus/online/desktop recovery loops remain. No new realtime event or backend work. Shared account-deletion composition and danger buttons are reused.

# Verification

Child PR #44 merged as c96d474211a21b586d5a1aed4142aa448256e291. Child UI verification passed 116 tests, 93 browser scenarios and build; final Link-only light/dark mobile/desktop screenshots reviewed.

VERIFY_BASE=738e6cf make verify-plan and make verify selected backend=True/frontend=full across 21 files for the complete open PR. All selected checks passed: 218 backend tests, 116 frontend tests, 93 browser scenarios, 7 production routes, 3 style-studio cases, hooks, initialization, architecture, environment/contracts, packaging and project build. No selected checks omitted. Live payment and native desktop actions were not repeated for this presentation-only follow-up. Current/pending subscription ownership and existing recovery loops remain unchanged.
