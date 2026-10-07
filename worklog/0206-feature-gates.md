# Commit Title

fix(config): enforce disabled feature boundaries

# Changed File Scope

Public configuration, authentication and billing guards, frontend routes/hooks, contracts and tests.

# Reason

Disabled integrations must not remain visible or issue provider requests. Verify Stripe startup failure blocks serving.

# Design

Expose effective billing flags in public config; use existing config owner to gate routes and requests. Audit email, login and OAuth on both sides; retain typed domain errors. No schema migration.

# Verification Plan

Run make verify-plan then make verify; add disabled-feature request assertions and startup failure regressions.

# Impact

Disabled features disappear; enabled features retain current behavior. No payment or email is sent during validation.

# Loop Alignment

Request/service/error loops retained; no new background tasks or domain mutations. Frontend owner/recovery paths honor feature flags.

# Verification

make verify-plan / make verify selected backend=True, frontend=full and passed. Backend: 269 tests; frontend: 130 Vitest, 156 UI, 9 production-route and 3 Style Studio tests. Hooks, architecture, environment contracts, lint, typecheck, API contracts, packaging and project build passed. Targeted feature/startup suite: 36 passed, including real SDK authentication rejection preventing lifespan completion/migrations. No required checks skipped. Request/service guards and frontend recovery/owner loops are preserved; background/event loops are not applicable because this task adds no asynchronous business operation.

Frontend integrated after B4React PR #57 merged as 89e668b4cd8ae185dfda98ad6ccac33965bd162e. Child pre-push full verification and actual PR governance passed; merge method was merge. The merged child source is identical to the root-verified working tree. Parent pre-push validates the full authored range.
