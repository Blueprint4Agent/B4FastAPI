# Commit Title

feat(deploy): integrate publication-ready frontend

# Changed File Scope

Pinned B4React gitlink, Docker build arguments/Compose/environment example and env contract classification, deployment/publication notes in English and Korean.

# Reason

Consume merged child MIT, audited dependencies and static sharing metadata, and expose public metadata configuration to the container build.

# Design

Pin child merge 4c5fb98581c8d5254cfbe91b901aef2a2beafd21 after B4React PRs 69, 70 and 71 merged. Pass optional public site URL and description only into the frontend build stage. Preserve API contracts and runtime configuration. Classify the two frontend build inputs as Docker-only relative to backend runtime templates.

# Verification Plan

Root make verify-plan then make verify against main, including parent packaging/contracts. Build a Docker image with explicit public metadata and inspect packaged HTML. Preserve existing external services/data.

# Impact

Requires image rebuild to update sharing values; no automatic deployment, DB migration or provider setup. Updated test tooling and compatible frontend dependencies come from the verified child.

# Loop Alignment

Backend request/domain-event/background-task loops unchanged: no backend behavior edits. Frontend API/realtime/desktop/composition loops remain child-owned and unchanged; static metadata introduces no state or API calls.

# Verification

Full root make verify-plan/make verify passed after npm ci installed the updated child lockfile (Vitest 4.1.11): backend 450, frontend 147, browser UI 188, production routes 10 and Style Studio 3 tests; contracts, packaging and project branding builds passed. No required checks omitted. An initial env-contract failure identified the two build-only keys and was fixed through explicit classification; an interim run was stopped to refresh stale installed dependencies before final evidence. Docker image build with an explicit public origin/description passed. Isolated local HTTPS readiness, signup/login, baked metadata including absolute image URL, Secure/HttpOnly cookies, UID 10001 and blocked metrics/docs/OpenAPI all passed. Compose app/worker/beat forwarding passed. Temporary containers/network/images removed; no live deployment, public DNS/ACME or external-provider certification claimed. Backend and frontend runtime loops are unchanged because this task only integrates merged child work and build configuration.
