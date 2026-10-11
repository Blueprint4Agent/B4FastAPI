# Commit Title

docs: introduce the blueprint with verified previews

# Changed File Scope

English/Korean README introductions and quick starts, actual showcase screenshots and publication guidance.

# Reason

The public entry point lists technologies but does not quickly show the product, intended workflow or configuration boundaries.

# Design

Lead with contract-based FastAPI/React development and agent workflow; show real isolated screenshots in both languages. Add reproducible clone/tool prerequisites and feature/configuration distinctions. No hosted demo URL or unverified production guarantee.

# Verification Plan

Review both screenshots, links and documented commands. Root Make verification across the branch; unchanged frontend receipts may be reused. No UI source changes.

# Impact

Documentation/assets only. Screenshot environment uses isolated disposable SQLite and disabled external integrations; no user data is included.

# Loop Alignment

No runtime loops change. Public examples describe existing API/state/event/worker flows rather than introducing new ones.

# Verification

- EN/KO screenshots captured from the actual pinned B4React packaged frontend (d32fce7) served by a disposable Docker app; both 1440x1000 images visually reviewed. No customer data or external integrations used; container removed.
- Root full-branch verify-plan/verify passed: 450 backend tests, existing frontend receipts reused, contracts/package/branding checks passed. No UI implementation changes.
- All local links in both README/publication guides resolve; quick start checked against Make targets and Python/Node requirements.
- No hosted demo or external deployment is claimed; MIT and provider/desktop/CI limitations remain explicit.
