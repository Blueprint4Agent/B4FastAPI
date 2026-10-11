# Commit Title

test(startup): isolate interactive terminal assumptions

# Changed File Scope

Interactive startup-display regression fixture and EN/KO backend test documentation.

# Reason

The readiness audit reproduced a failure under TERM=dumb despite force_terminal=True because Rich still identifies a dumb terminal.

# Design

Declare the interactive terminal capability inside the test with monkeypatch, which restores the environment afterward. Preserve assertions for warning visibility and final rendered frame. No runtime display behavior changes.

# Verification Plan

Root make verify-plan/verify using TERM=dumb and a focused interactive test under xterm. Retain full branch checks with content-bound frontend receipts.

# Impact

Tests no longer require developers to export a particular TERM globally.

# Loop Alignment

Test-fixture-only change; runtime request/event/task and frontend loops are unchanged.

# Verification

- TERM=dumb root verify-plan/verify against origin/main passed: full branch scope, 450 backend tests. Unchanged frontend evidence reused through receipts; contracts/package/branding passed.
- The focused interactive-display test also passed under TERM=xterm-256color. The test retains warning and final-frame assertions.
- No application runtime or external service changes; no live integration checks were needed for this fixture-only change.
