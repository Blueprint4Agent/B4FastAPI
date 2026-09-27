# Commit Title

feat(setup): initialize projects from a shared manifest

# Changed File Scope

Project manifest example, initializer/tests, Make/CI, documentation and pinned B4React.

# Reason

Make a copied blueprint configurable from one public project manifest instead of manually replacing names, branding, desktop identity and feature flags.

# Design

Parent owns a validated project manifest and plan/apply/check CLI. Reuse env parsing/rendering and back up modified local files; preserve unrelated settings and credentials. Generate a public child-local project.local.json plus optional logo assets. B4React consumes only its own local config through Vite and the Tauri launcher; no source or package-lock rewriting. Public identity generation is shared by initialization, root frontend builds and a standard-library Docker stage. Parent CI includes a temporary configured frontend build so generated assets stay reproducible. Defaults retain the template identity. Backend feature switches remain the existing config authority. Reject invalid manifests before writes; repeated initialization is idempotent.

# Verification Plan

Fixture tests for manifest validation, env preservation, fresh initialization, idempotence, drift detection and write failures; child branding/HTML/Tauri configuration tests and configured production browser smoke. Root make check test build, child check/test/build/test-ui/test-routes, staged governance and required CI. Native bundle compilation is not required for configuration-only launcher changes; verify merged Tauri config directly.

# Impact

Opt-in initialization for fresh copied projects. No automatic configuration of this working application's real env, no schema or API change. Existing make init remains env-only. Native package identifier/product name are configurable; source package/crate/module names stay stable.

# Loop Alignment

Existing API/auth feature/recovery loops remain authoritative. Build-time brand data is immutable, no new API/global state. Shared BrandMark/BrandBanner compose existing UI and showcase. Backend domain/event/task loops are not applicable to setup tooling.

# Verification

Passed root make check test build: initializer 9 tests, backend 82 tests, frontend 79 tests, formatting/types/architecture/API contracts and packaging. Child make check/test/build and config fixtures passed; make test-ui/test-routes passed 54 UI and 5 production browser tests. make project-build-test passed the configured Korean/English brand, logo/favicon and mobile checks (79 frontend tests plus 5 production browser tests) in an isolated temporary copy. Default entry stayed 390.76 kB / gzip 121.26 kB. No real env files or project identity were changed. Native packaging was not run because this change only merges launcher configuration, which is fixture-tested. make docker-build passed including the new public branding stage and full app image. Required PR checks run before merge.

B4React PR #21 merged with successful Frontend checks and Git governance; parent pins merge commit 26c56e0e48fb7415adb8900ebb95b9ee00452afd. MERGE auto-merge method was verified.
