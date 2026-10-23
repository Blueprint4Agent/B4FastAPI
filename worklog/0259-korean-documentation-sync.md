# Commit Title

docs: synchronize Korean workflow documentation

# Changed File Scope

Documentation only: Korean AGENTS translation/sync, README navigation and scoped-validation wording, WebSocket Korean example, and verification contract guidance. No footer/UI/runtime changes.

# Reason

Audit found missing child Korean AGENTS, omitted parent Korean workflow/hook/page-family sections, missing README navigation and mandatory-full-check wording inconsistent with scoped verification.

# Design

Translate current repository rules without changing policy. Preserve canonical child document redirects and existing destinations. Synchronize English/Korean navigation and distinguish ordinary docs from governance guides.

# Verification Plan

Check Markdown local links and locale document counterparts. Finish edits before measuring make verify-plan / make verify at root and child; record scope/wall times and governance-only selection. User subsequently authorized commit/push/merge: publish the child ready PR first, then integrate its merged pin in the parent; validate staged and actual PR metadata.

# Impact

Documentation accuracy/discoverability only; application CSS and pages are restored unchanged.

# Loop Alignment

Documentation-only: runtime API/realtime/desktop/UI composition and backend request/event/task loops are not applicable.

# Verification

Root make verify-plan / make verify passed (governance-only): measured wall 27.396 s, runner 27.2 s; parent harness 14.1 s and delegated child harness 12.6 s (run-cj9qkrt3). Neither command reused receipts in this first run. AGENTS translations intentionally require governance fixtures; no application UI/API/browser/build/deploy checks were selected. Markdown local file-link scan across root/child guides, notes and contracts found zero missing targets. Child Korean AGENTS now exists; parent Korean rules include missing scoped-validation, merge, task-order, hook/receipt and page-family sections. README navigation/validation guidance and WebSocket example are synchronized. Footer application sources/styles match HEAD. Initial local review did not stage or publish changes. The user subsequently authorized publication; reuse matching proofs and require local hooks/actual PR metadata governance before merge.

Child B4React PR #99 merged first at dd010e3073f60cc83ffdd7da445cda838147c668; parent pins that verified documentation tree.
