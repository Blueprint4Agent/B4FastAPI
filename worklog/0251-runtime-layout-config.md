# Commit Title

feat(config): expose runtime deployment layout

# Changed File Scope

Backend settings/config contract, environment examples, EN/KO runtime docs, pinned frontend and tests.

# Reason

Select a deployment layout through APP_LAYOUT without rebuilding the same image.

# Design

Backend Settings validates sidebar/topnav/focused and exposes app_layout through the existing no-store /config response. The shared frontend config snapshot owns the deployment default; development-only browser previews override it. Missing/invalid remote layout falls back to the source default for older providers. Appearance provides a reset action to clear a saved browser preview and follow the deployment default. No DB, new endpoint, store, polling or background work.

# Verification Plan

Run make verify-plan and make verify. Cover settings validation, /config values, deployment default precedence, config refresh preserving drafts, and the same production build in all three layouts. Synchronize EN/KO deployment instructions and contract snapshots.

# Impact

Additive optional response field with sidebar default. Changing the environment requires container recreation and browser reload, not an image rebuild. Production ignores browser preview state.

# Loop Alignment

Existing settings-to-config request path and shared API state loop are reused. UI composition reuses the existing three shells. No realtime event or background/desktop recovery changes are required for process-level configuration.

# Verification

B4React PR #89 merged as 8572a367fc12d3de5dfffd27ac0e26d2d013f9fa. Root make verify-plan selected backend plus full frontend integration. make verify passed project/environment/architecture/lint checks, 502 backend tests (58.57s), OpenAPI parity, frontend packaging (0.1s) and project build (12.6s). Matching child evidence was reused: 203 unit/component, 240 browser, 14 production route, 11 discovery and 3 Style Studio cases. No selected checks omitted. No new domain events, task loop or desktop recovery logic is applicable to this process configuration. Live diagnosis confirmed APP_LAYOUT=topnav and /config.app_layout=topnav; a stored sidebar preview masked them. Clearing only that browser preference restored topnav, and the new Appearance reset action was exercised against the live local app.
