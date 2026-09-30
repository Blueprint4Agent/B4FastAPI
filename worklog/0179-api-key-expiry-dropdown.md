# Commit Title

fix(frontend): integrate API key expiry dropdown correction

# Changed File Scope

Pinned B4React frontend revision and integration worklog.

# Reason

Prevent expiry options from being clipped inside the API-key modal and warn when No expiration is selected. Sidebar work was merged into main first in PR #74 (9e25f0f).

# Design

Integrate a separate child fix PR based on merged sidebar changes. Modal menus render in the dialog layer outside the scrolling panel, retain accessible interaction and fit the viewport. A controlled warning uses the existing InlineMessage.

# Verification Plan

Run root verify-plan and remaining root Make integration targets; reuse unchanged successful full child make verify evidence per policy. Validate ready PR metadata and required CI before merge.

# Impact

No API lifetime/payload or backend changes. Finite expiry hides the warning. Shared modal clipping and fixed footer remain intact.

# Loop Alignment

UI composition extends shared DropdownMenu/Modal and reuses InlineMessage. Expiry state stays page-owned. API, realtime, desktop recovery and backend request/event/background loops add no new behavior and are not applicable.

# Verification

Full child make verify passed; make test after the additional focus regression passed 98 tests, and final make check passed. Browser suite: 71 cases; production routes/build: six; style studio: three. Root verify-plan selected full frontend scope with no backend scope. Reused unchanged child results per no-repeat policy and ran root make verify-light frontend-contract-check frontend-package-verified project-build-test successfully (including six isolated custom-branding production cases). The full root runner would duplicate completed child targets, so executed its remaining root Make targets. Backend checks omitted because static frontend behavior changes no server contract or state. Live before/after body metrics stay clientHeight=140 / scrollHeight=140, compared with previous scrollHeight=282 while open. Korean menu and warning screenshots visually reviewed. Child PR https://github.com/Blueprint4Agent/B4React/pull/32 passed Git governance and Frontend checks and merged as 27df2879410fba5c0ee07754483283874b8ff079. Its tree matches tested child commit 447437f.
