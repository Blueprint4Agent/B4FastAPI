# Commit Title

fix(frontend): integrate plan currency toggle

# Changed File Scope

src/frontend gitlink and integration worklog.

# Reason

Integrate the simpler plan header, compact $/₩ selector with subscriber preview switching and showcase, and remove the pending-plan card from plan selection.

# Design

Merge the child PR first, then pin its merge commit; child owns source, browser coverage and localized docs.

# Verification Plan

Root make verify-plan and make verify with child UI coverage and parent contract/package validation.

# Impact

No backend or API changes; existing subscription currency remains authoritative.

# Loop Alignment

Presentation-only integration; API state, realtime, desktop recovery and backend lifecycle/event/task loops are unchanged.

# Verification

B4React PR #51 merged at 70be4f30545460b5fb8b8cfd8ecf80f50e641423. Root make verify-plan selected full frontend scope. make verify passed governance hook fixtures, child 122 tests and 114 UI browser cases, 7 production-route cases/build, style-studio fixtures and 3 browser cases, contract checks/static packaging and project build fixtures. Child visual review covered 390/1440px in both themes, Korean labels, subscriber dollar preview, no pending banner and 44px touch targets. Backend checks are omitted because this change has no backend/API implementation changes; API, realtime, desktop recovery and backend loops remain unchanged.
