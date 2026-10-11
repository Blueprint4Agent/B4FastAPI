# Commit Title

feat(frontend): integrate the B4A preview browser

# Changed File Scope

Manual GHCR build inputs, frontend gitlink, Docker build arguments/environment example, public environment key classification, EN/KO deployment notes and integration worklog.

# Reason

Improve project exploration, list actual platform capabilities, make hero actions consistent, correct branding to B4A and support optional development-only Buy Me a Coffee links.

# Design

Merge the child preview browser first, pin its merge commit, then rebuild the local monolith. Child owns thumbnails, shared Modal viewer and navigation permissions. Forward optional public Buy Me a Coffee enabled/URL build arguments from Compose and explicit manual GHCR workflow inputs to the frontend, default disabled. The frontend additionally requires server development mode; production always hides both home and sidebar support links.

# Verification Plan

Root make verify-plan and make verify. Reuse unchanged child verification; retain parent contract/packaging checks. Verify the rebuilt home at localhost:18000 and publish/inspect the GHCR image through the manual Build workflow.

# Impact

Frontend presentation only; existing environment values and data volumes retained.

# Loop Alignment

Existing auth/config owners retained. Static previews have no backend API, realtime or background task changes; UI composition follows child Button/Modal policy.

# Verification

Merged B4React PR #73 at 6e08cde1aa86aa033c4a8faf18894d6ec5b6ed7a. VERIFY_BASE=aa0e6729 make verify-plan and make verify passed (backend=True, frontend=full): 459 backend tests, environment/architecture/OpenAPI checks, packaging and 10 fresh project-build production routes. Unchanged child receipts reused 165 unit/component/integration tests, 191 browser cases, 10 route cases and 3 style-studio checks; no manual scope downgrade.

Built and started the local Docker image successfully. localhost:18000 verified four decoded previews, enlarged viewer/Escape, smooth scrolling, eight capabilities, B4A branding, mobile width and two configured support links. Top support is 113px wide and 32px high at desktop size. Local public coffee values match the frontend .env; all other values and persistent volumes were preserved. Actual localhost:5173 was also checked.

GHCR publication is performed after this PR merges using the manual Build workflow (ref=main, publish_image=true, coffee_enabled=true, configured public creator URL). The workflow runs fresh full checks before publishing; registry digest is verified after completion. No AWS/Cloudflare resources were provisioned.
