# Commit Title

feat(home): refresh feature overview and role-aware navigation

# Changed File Scope

Home overview/locales/shortcuts, profile menu visibility, showcase sidebar icon, read-only synthetic inquiry demo, role/browser tests and localized documentation. Parent integrates the merged child gitlink.

# Reason

Expose recently added inbox, inquiries, profile and realtime capabilities and remove the redundant demo entry for administrators.

# Design

Reuse the existing home capability grid and shortcut family. Add concise accurate descriptions: SSE is connected; WebSocket is an opt-in provider template. Hide only the administrator demo menu for admin role while retaining the real panel and public demo for others. The inquiry demo reuses the real inquiry composition with localized synthetic fixtures; disable HTTP reads/writes and hide mutation controls. Use the Blocks icon for the component showcase.

# Verification Plan

Root make verify-plan/verify; role menu regressions, mobile/desktop light/dark home comparisons and shortcut destinations.

# Impact

Frontend presentation/navigation only. No API, schema, permissions or image build changes.

# Loop Alignment

Existing auth/config snapshots own role and visibility. No added requests, realtime subscriptions or desktop recovery path. Reuse home grid, sidebar links and icons.

# Verification

Root make verify-plan/verify selected full frontend verification with backend=False. Typecheck/static/policy checks passed; 168 frontend tests, 212 browser tests and 10 production route/branding tests passed. Style-studio, contracts and packaging checked. Focused home/demo run passed 26 tests; demo makes zero inquiry API requests, hides mutations and rejects direct routes when disabled. B4React PR #81 merged at 4db7b4769fd72cab06590fb4513511f51dbb7bfd with a merge commit. Parent integration reuses matching receipts and validates packaging. Backend tests omitted by classifier because no backend/API/schema code changed. No Docker/GHCR build, per user preference.
