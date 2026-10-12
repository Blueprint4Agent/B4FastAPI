# Commit Title

fix(admin): move demo entry into profile menu

# Changed File Scope

Merged frontend gitlink and English/Korean deployment documentation.

# Reason

Place the demo beside the existing administrator entry as requested, rather than in the main sidebar navigation.

# Design

Pass a demo-enabled boolean from AppSidebar to ProfileDropdown. Reuse the existing administrator link structure with the label Admin panel (demo) and /demo/admin destination. Keep real administrator access independent. Remove only the main sidebar entry; retain demo section navigation and home preview links.

# Verification Plan

Run make verify-plan and make verify for the full branch range. Existing demo browser cases exercise dropdown navigation, disabled visibility and administrator peer geometry.

# Impact

Navigation-only change; API/config/data behavior unchanged. No image build or publication for this patch, per user preference.

# Loop Alignment

Existing menu state, pathname dismissal and UI composition remain owners. API/realtime/connectivity behavior is unchanged; no backend lifecycle/event/task changes.

# Verification

B4React PR #75 merged with merge commit f9ea3140d639b27a2e4df4a87f786c6a4dcaddec; pin that commit. Child Make verification passed check, 165 unit/component/integration tests, 196 browser tests and web build. Parent selected UI verification plus contract/packaging integration; make verify passed all selected checks, reusing unchanged child receipts and running parent contract/packaging checks. No selected checks omitted. Backend tests are not selected because backend source/config/data behavior is unchanged. No API/realtime/event/task loop changes.

The previously started image workflow 38226900415 was canceled before image publication when the user requested no automatic image build. This patch does not dispatch a build.
