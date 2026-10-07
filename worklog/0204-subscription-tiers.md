# Commit Title

feat(billing): separate subscription tiers and billing intervals

# Changed File Scope

Billing models, pricing configuration/service, local OpenAPI contract, pricing/settings/sidebar UI, tests and bilingual billing documentation.

# Reason

Separate Free/Plus/Pro product tiers from monthly/annual billing and show the server-confirmed tier on the sidebar profile.

# Design

Preserve legacy monthly/annual price IDs as Plus, add Pro purchase keys while mapping tier and interval independently in the UI. Server owns amounts and subscription identity. Pricing reuses the standalone plans family and shared SegmentedControl; profile badge reuses avatar composition. Each paid card owns its interval selector. Annual prices use roughly 10 percent discount; existing subscribed prices are preserved. Plus-to-Pro upgrades use immediate prorated pending updates; downgrades/cancellation and same-tier cycle changes remain period-end. Pending payments retain the old tier and show an explicit recovery action.

# Verification Plan

Run make verify-plan then make verify in child and parent; provider-mocked tier/interval and ownership tests; desktop/mobile pricing and sidebar UI comparisons.

# Impact

Existing Plus subscriptions retain their provider price IDs and billing schedule. No automatic migration or charge. New Pro purchases require configured provider prices.

# Loop Alignment

Backend router/service/provider validation stays authoritative; no new DB schema. Frontend API owners retain account reset, async isolation and connectivity recovery. Billing changes refresh the profile tier. No billing SSE/background entitlement projection is introduced.

# Verification

make verify-plan selected backend=True and frontend=full. make verify passed backend architecture/environment/contracts and 239 backend tests; delegated frontend checks passed 126 tests, 143 browser UI tests and 9 production route tests. Matching local Style Studio evidence (3 tests) was reused. Frontend contract/package and project-build integration passed. No required scope was omitted.

Actual Stripe sandbox probes verified successful prorated Plus-to-Pro upgrades and declined-payment pending updates retaining Plus with a recovery URL. The latter exposed Decimal serialization in pending-update data; the version fingerprint now uses the expiry timestamp and a regression fixture covers the response. All temporary sandbox subscriptions/customers were cancelled/deleted. Configured Plus/Pro catalog prices were retained; existing user subscriptions were not migrated. Local .env was synchronized without committing secrets.

Frontend loops, state ownership and page-family comparisons are recorded in B4React worklog/0062-subscription-tiers.md. No database migration, billing SSE or background entitlement projection was added because Stripe remains the state owner and changes are reflected through authenticated reads/invalidation.


Integrated B4React PR #55 at merge commit 62db9de95e07ddc187933c644c340a3441e266f0 after actual PR governance validation.
