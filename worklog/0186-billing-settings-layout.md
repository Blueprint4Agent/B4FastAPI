# Commit Title

fix(frontend): integrate consistent billing settings layout

# Changed File Scope

Frontend gitlink, bilingual billing guide and integration worklog.

# Reason

Billing used oversized independent surfaces and duplicated header spacing instead of matching existing settings.

# Design

Integrate child use of shared settings header/content and row surfaces. Preserve billing state and actions. Browser comparisons check billing against general settings.

# Verification Plan

Child scoped Make verification and desktop/mobile visual checks; parent branch make verify-plan and make verify plus governance.

# Impact

Consistent settings layout with no API or entitlement changes.

# Loop Alignment

UI composition reuses existing settings classes. API state/realtime/desktop recovery unchanged; backend loops are not applicable to this presentation change.

# Verification

B4React PR #38 merged at d77b696. Child UI scope passed 110 tests, 79 browser scenarios and build; General/Billing geometry and surface comparisons passed at 390/1440px in light/dark. Desktop/mobile screenshots inspected. VERIFY_BASE=8d5e2f7 make verify-plan selected backend + full frontend; make verify passed hooks, backend/contract checks (189 tests), frontend check/test, UI, production routes (7), style studio (3), packaging and project build checks. No selected checks omitted. Real provider writes/native packaging excluded because this task changes presentation only.
