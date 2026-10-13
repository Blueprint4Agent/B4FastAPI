# Commit Title

feat(frontend): integrate service layout modes

# Changed File Scope

Pinned B4React gitlink, frontend integration documentation and this worklog.

# Reason

Let service authors choose sidebar, top navigation or focused layouts and preview all three from Appearance in server development mode.

# Design

Keep sidebar as the service default in src/service.config.ts. Share navigation, authorization and profile controls across three shell presentations. A scoped provider owns the validated browser-local development preview; production and unknown server modes always use the service default. Reuse SelectionCard and settings row composition. Settings/admin context menus stay out of global top navigation: use a boxed left navigation beside content, with a mobile disclosure. Verify home/profile/inbox/auth and recovery shells too. No backend contract changes.

# Verification Plan

Run make verify-plan and make verify; inspect browser mobile/desktop light/dark layout, keyboard and profile navigation; verify production ignores stored previews. Run parent integration checks after the child merge.

# Impact

Existing sidebar remains default. Development preview persists only in this browser and does not modify deployment defaults. Topnav and focused retain settings/profile/login and role-filtered navigation.

# Loop Alignment

UI composition reuses shared controls and navigation. API state and realtime ownership remain unchanged; no new requests or background tasks. Desktop recovery status and offline logout guard remain reachable in every layout. Backend event/task loops do not apply to this frontend-only behavior.

# Verification

B4React PR #85 merged with merge commit 57df9dd5cd2a0d6447205572361c73a45f609dcc. Child full verification passed 195 unit/component/integration tests, 227 UI browser cases, 10 production-route cases, 11 discovery cases and 3 style-studio cases plus policy/type/format checks. Root make verify-plan selected full frontend integration, backend=False. Root make verify passed hook tests, project branding, contract equality, verified dist packaging and isolated custom-brand production build. Content-bound receipts reused unchanged child checks instead of repeating them. Backend tests and native Rust builds are omitted because no backend/native behavior changed. API/realtime/desktop recovery ownership stays unchanged; UI composition uses the shared shell and controls. Git governance and actual PR metadata checks are required before merge.
