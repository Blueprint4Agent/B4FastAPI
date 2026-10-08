# Commit Title

feat(admin): expose safe object storage status

# Changed File Scope

Admin storage status schema/service/router, safe metadata, tests, contract, docs and frontend integration.

# Reason

Show configured object storage alongside existing server dependencies without exposing deployment identifiers.

# Design

Reuse admin-only status API and cached single-flight integration checks. Project only provider enum, transport enum, port, probe scope, timestamp and measured latency. Never expose paths, buckets, endpoints, credentials or raw failures. Reuse existing settings rows and locally served logos.

# Verification Plan

Root verify-plan/verify; auth, sanitization, failure/cache tests; mobile/desktop light/dark peer comparisons and provider logo tests.

# Impact

Additive admin contract; no migration or storage configuration changes. Remote checks use HeadBucket only; local checks use temporary write/read/delete probe.

# Loop Alignment

Existing admin polling/recovery remains owner. Request/service/provider lifecycle retained; no event or background task needed for an on-demand cached read.

# Verification

Root make verify-plan selected full backend/frontend scope; make verify passed: hooks, initializer, architecture, env contract, Ruff, 352 backend tests, OpenAPI contracts, 147 frontend tests, 169 UI tests, 9 production route tests, 3 style-studio tests and integration build/packaging. Backend verification uses the existing isolated Python 3.13.13 environment because the original interpreter was observed exiting 137. Provider/redaction/cache/failure checks use mocks; no remote cloud writes. No selected checks omitted. Child PR #65 merges before parent gitlink. Parent PR is stacked on the still-open profile-photo PR #110 to keep this scope separately reviewable. Per-user feedback, UI row explanation and timestamp were removed; safe metadata and actual cached status remain.
