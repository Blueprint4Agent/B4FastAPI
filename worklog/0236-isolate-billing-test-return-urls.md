# Commit Title

fix(tests): isolate billing return URLs from local environment

# Changed File Scope

Shared backend Stripe fixture, EN/KO testing documentation and worklog.

# Reason

GHCR Build run 38130358914 failed 22 billing cases in a clean runner while local tests passed. Existing registration fixtures set setup URLs but inherited subscription checkout return URLs from the developer .env; clean defaults are blank, making billing configuration unavailable.

# Design

Set deterministic localhost subscription return URLs in the existing autouse Stripe isolation fixture. Tests still explicitly enable a mocked provider, and individual invalid-configuration tests may override these values. No runtime, API, schema or migration changes.

# Verification Plan

Reproduce a failing registration test with empty checkout URL environment variables, then repeat billing tests and root make verify-plan/verify with the same clean values. Run the manual GHCR build again after merge.

# Impact

Tests no longer depend on a developer checkout URL. No real credentials or provider requests are introduced.

# Loop Alignment

Request, event and background loops are unchanged; test fixture-only change. Frontend loops are not applicable.

# Verification

Reproduced BILLING_DISABLED in test_setup_has_no_charge_and_reuses_request_key with both checkout URL environment variables empty. After fixture isolation, the same empty environment passed make verify-plan and make verify: backend=True, frontend=docs; all 459 backend tests, architecture/environment checks and OpenAPI contracts passed. Frontend runtime checks omitted by the classifier because no frontend code changed.
