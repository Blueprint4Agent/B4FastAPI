# Commit Title

fix(docker): harden containers and add an HTTPS entrypoint

# Changed File Scope

Dockerfile, base Compose, optional HTTPS Compose/Caddy configuration and EN/KO deployment guidance.

# Reason

The app runs as root and exposes its HTTP/metrics port on all interfaces without a supplied public HTTPS entrypoint.

# Design

Run API/worker/Beat as UID/GID 10001 with writable data directories; drop Linux capabilities and disable privilege escalation. Bind base app HTTP to loopback. Provide opt-in Caddy TLS with protected metrics/docs and explicit trusted-proxy settings. Keep TLS setup separate from local deploy commands; no public DNS or ACME changes during implementation.

# Verification Plan

Root Make verification; Docker image build; nonroot SQLite/object-volume recreation probe; Caddy config validation and isolated local TLS/proxy checks. Review compatibility and permission migration instructions.

# Impact

Direct public access to port 8000 stops by default. Existing root-owned data volumes require an operator-reviewed ownership migration. Optional proxy trusts forwarded headers on the private deployment network; only trusted services may join it. No automatic permission changes or live rollout.

# Loop Alignment

Startup verifies writable storage before requests. Proxy preserves streaming for realtime; application request/event/task/frontend behavior is otherwise unchanged. Worker and Beat retain dedicated persistent storage.

# Verification

- Root verify-plan/verify selected full scope against origin/main and passed; 450 backend tests passed with TERM=xterm-256color. Unchanged frontend checks reused receipts; integration/branding passed.
- Docker image built. Fresh named-volume SQLite/object storage started as UID 10001 and retained a marker after container recreation; probe resources removed.
- Base/HTTPS Compose models validated. Caddy config validated against the pinned image version 2.11.7.
- Isolated localhost TLS probe: readiness and SPA 200, metrics/docs/OpenAPI 404, signup/login 200 and refresh cookies Secure + HttpOnly; app UID 10001. Probe resources removed. Initial internal-network probe could not publish a host port; repeated on a dedicated bridge bound to loopback.
- No live DNS, public ACME, provider callbacks or existing-volume ownership changes. Those require deployment-specific configuration and are not claimed by the local smoke test.
