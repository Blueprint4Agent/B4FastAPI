# Commit Title

fix(ci): pin browser verification to ubuntu 24.04

# Changed File Scope

.github/workflows/build.yml and English/Korean verification documentation.

# Reason

GHCR publication run 41057030136 failed because ubuntu-latest resolved to Ubuntu 26.04, unsupported by pinned Playwright 1.59.1.

# Design

Pin only the frontend browser verification job to ubuntu-24.04; preserve all checks and publication dependency gates. Backend and image build jobs retain their existing runners.

# Verification Plan

Root make verify-plan and make verify, staged governance, real PR validation, then rerun the manual publication workflow after merge.

# Impact

Restores browser installation on a supported distribution without skipping verification or changing app/runtime behavior.

# Loop Alignment

CI environment change only; backend request/event/task and frontend API/realtime/desktop/UI loops are unchanged.

# Verification

- Failed remote run 41057030136: frontend browser installation reports Playwright 1.59.1 cannot install Chromium on ubuntu26.04-x64; backend checks passed, image publication was skipped.
- Installed Playwright dependency metadata includes ubuntu24.04-x64.
- Branch-wide REDIS_IN_MEMORY=true make verify-plan selected all areas; make verify passed all 15 commands, including complete backend, frontend application, style studio/discovery, branding, contracts and packaging. Unchanged application checks reused valid receipts.
- Remote publication verification follows merge; no checks were disabled. No runtime/domain-loop changes.
