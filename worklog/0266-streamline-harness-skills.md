# Commit Title

docs(harness): streamline workflow skills and guidance

# Changed File Scope

Parent AGENTS, localized guidance, GitHub PR templates, repository skills, verification classifier and its tests; inspect child guidance without editing its pin.

# Reason

Reduce repeated instructions and resolve conflicting workflow requirements while preserving executable enforcement.

# Design

Keep invariant policy in AGENTS, operational Git procedures in three repository skills, output schemas in existing templates, and enforcement in Make/hooks. Audit broader guide contradictions against code.

# Verification Plan

Run make verify-plan and make verify; validate skill manifests and changed classifier ownership; staged and actual PR governance checks before publication.

# Impact

No application behavior or live ruleset changes. Preserve initialization trigger, child-first integration and GitHub forms.

# Loop Alignment

Backend request/event/task and frontend API/realtime/recovery/UI loops are not applicable: governance/documentation only; no runtime paths changed.

# Verification

Final make verify-plan / make verify passed with governance + harness ownership: 55 verification fixtures and 8 hook fixtures. All three skill manifests passed skill-creator quick_validate; Ruff check/format passed for both changed Python files; git diff --check passed. Runtime/backend/frontend/browser/build suites were omitted by the classifier because no application or contract behavior changed. AGENTS shrank from 251 to 93 lines; duplicated historical benchmark prose now links its existing worklog. Staged governance and normal hook publication are required before PR completion.

## Harness audit (2026-10-30)

Resolved in parent:
- AGENTS, README and PR templates repeated commit/PR mechanics: route to three repo skills; retain GitHub output templates and Make/hook enforcement.
- AGENTS described commit bodies as non-trivial-only, but validate_git_governance.py requires them for every authored commit: document actual enforcement.
- Backend sections 1/6 mandated formatting mutations and manual minimum tests: use the scoped Make plan and optional formatting fixes.
- PR verification checkboxes implied all backend/frontend/build suites always ran: ask for selected scope, observed results and task-specific omissions.
- README and frontend-submodule guides demanded provider/consumer equality and adoption for all additions: align with verification_contract.py's strict additive rule; existing schema changes still require coordination.
- Submodule instructions duplicated check/test/build despite scoped verification and receipt reuse: use the planner, preserving child-first integration and parent responsibilities.
- Backend architecture guide claimed a required CI job: align with checked-in workflow_dispatch workflows and ruleset. Live protection was not changed or audited.
- Universal business-layer wording conflicted with explicitly allowed technical/transport adapters: clarify the existing exception, without adding wrapper services.
- Auto-merge wording required inspecting registration before it existed: PR skill inspects after registration, or verifies immediate merge outcome.
- Historical benchmark tables duplicated worklog 0211: link the preserved measurements instead of maintaining another copy.
- Skill Markdown would otherwise become ordinary text: register repository skill Markdown as governance; executable skill files remain conservative unknown/full.

Remaining child-owned findings (no child source or gitlink changed):
- src/frontend/FRONTEND.md:327-329 still describes a required Frontend checks job despite the manual-only policy in the child's AGENTS.md. Correct in a B4React PR.
- src/frontend/AGENTS.md repeats workflow/hook prose; migrate independently using child templates and child governance, not parent-only skills.
- Parent notes/ko/backend/BACKEND.md omits the English Automated Layer Boundaries section. Existing English guidance remains authoritative; full translation parity beyond the edited workflow sections is a follow-up, not claimed complete.

Skill review scenarios: commit-only ends before publication; PR-only reuses existing head PR; issue-only reads the selected existing template and does not demand a file commit; review-only does not publish; ambiguous remote creation is read back before retry; B4React work routes to its own guides. No test issues or PRs were created for these dry reviews.
