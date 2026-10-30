# Commit Title

fix(ci): install python tooling for frontend branding checks

# Changed File Scope

Build workflow, English/Korean verification docs and worklog.

# Reason

Publication run 41057591229 passed frontend tests but failed project-init-check because the frontend job did not install uv.

# Design

Install uv, Python 3.12 and frozen backend dependencies before frontend verification, matching the project-init/project-build tools actually selected by full CI. Keep all publication gates.

# Verification Plan

Branch-wide make verify-plan and make verify; staged/PR governance; rerun full remote publication after merge.

# Impact

CI dependency provisioning only. No runtime, data or user-interface change.

# Loop Alignment

No application request/event/task or frontend API/realtime/desktop/UI loop changes.

# Verification

Branch-wide REDIS_IN_MEMORY=true make verify-plan selected all areas; make verify passed all 15 commands, including project initialization/branding builds, backend suite and contracts/packaging. Valid unchanged frontend receipts were reused. Remote run 41057591229 passed all browser suites before failing on missing uv; rerun publication after merge. No selected checks omitted.
