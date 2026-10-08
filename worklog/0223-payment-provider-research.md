# Commit Title

docs(billing): assess additional payment providers

# Changed File Scope

English/Korean provider research notes, README navigation and this worklog only.

# Reason

Issue #94 asks for an evidence-backed feasibility decision after #93, without choosing a provider before merchant/country/payment/settlement requirements are known.

# Design

Compare the current Stripe implementation with Toss Payments, PortOne and Paddle using current official sources. Separate verified template requirements from unconfirmed commercial requirements. Map backend/model/webhook/frontend coupling, capability interfaces, coexistence and card/Link/subscription migration limits. Recommend deferring adoption until requirement gates are resolved; no accounts, contracts, payments, provider code or abstractions are created.

# Verification Plan

Check primary sources and checked-out code, link English/Korean documents from README, run root make verify-plan then make verify and Git governance. No sandbox PoC needed for a deferred adoption decision; #93 read-only sandbox evidence is linked rather than repeated.

# Impact

Research-only decision record, no runtime/API/schema/billing changes. Prices are dated public examples, not merchant quotes or a claim of account eligibility.

# Loop Alignment

Request lifecycle, domain events, background tasks, frontend API/realtime/desktop/composition loops are unchanged; proposed extensions are documented only. All runtime loops are not applicable to this documentation change.

# Verification

- Official provider pricing, billing, sandbox, verification, settlement and Stripe export sources inspected on 2026-10-08; URLs are embedded beside supported claims in both languages.
- Checked current service/model/router/frontend dependencies directly at f608b46 / d4878ea.
- Local research links and git diff --check passed; README points to both locales.
- make verify-plan then make verify passed: backend=False/frontend=docs, four text files. Runtime tests, dependency install, build and browser checks omitted by the documentation-only classifier; runtime loops unchanged.
- No provider account, contract, new adapter, migration, payment/refund or email created. Adoption is explicitly deferred pending commercial requirements, not marked implemented.
- Planned and actual PR governance required before merge.
