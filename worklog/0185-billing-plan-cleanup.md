# Commit Title

style(frontend): integrate cleaner billing plan layout

# Changed File Scope

Frontend gitlink, bilingual billing integration guide and parent worklog.

# Reason

Simplify the plan UI and remove the redundant back-to-billing action requested by the user.

# Design

Remove back navigation, eyebrow, redundant currency label and decorative card icon/headline. Keep plan names, descriptions, prices, selection actions. Present the template-price disclosure as quiet readable footnote text rather than an alert card. Move /plans outside AppLayout into a full-window scroll surface with a top-right accessible close action and bounded internal return destination. Signed-in Free remains the current template plan with a disabled Current plan action; URL selection cannot promote a paid candidate into the active subscription. Use a compact shared dropdown at the cards’ upper right and remove the plans registration footer. Card/Link registration remains in Settings Billing. No billing API changes.

# Verification Plan

Run make verify-plan and make verify, existing browser layout/registration tests and visual screenshot review. Parent validates packaging/contracts after child merge.

# Impact

Cleaner plan comparison with less repeated copy. Example-price and no-subscription disclosures remain visible.

# Loop Alignment

UI composition retains shared Button and app.css. API, realtime and desktop recovery behavior is unchanged; no backend/event/task changes.

# Verification

B4React PR #37 merged with a merge commit at 8c2481b. VERIFY_BASE=8d5e2f7 make verify-plan selected backend + full frontend scope; make verify passed all selected hooks, backend/architecture/environment/contracts (189 tests), frontend (110 tests), browser UI (79), production routes (7), style studio (3), packaging/contracts and project build tests. Child desktop/mobile screenshots reviewed. No selected checks omitted. Real Stripe writes and native packaging omitted because this task only adjusts presentation and route composition.
