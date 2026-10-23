# Commit Title

feat(onboarding): add repository-native agent initialization flow

# Changed File Scope

- AGENTS.md and notes/ko/AGENTS.md: natural-language initialization routing.
- PROJECT_ONBOARDING.md and notes/ko/PROJECT_ONBOARDING.md: intake, execution, resume and verification flow.
- PROJECT_SETUP.md, README.md and Korean counterparts: discovery and command/workflow boundaries.

# Reason

A developer starting a fork needs the repository agent to collect project intent, screen references, branding and language choices before applying the existing initializer and project-specific UI/document changes. The workflow must travel with the repository without installing a skill.

# Design

Route an explicit initialization request from AGENTS.md to a repository-owned guide. Collect missing inputs one stage at a time, persist public decisions and progress in PROJECT_BRIEF.md, then use existing manifest/Make targets and domain guides for implementation. Keep product, documentation and conversation language independent. Distinguish supported generated identity from source changes, native icons and document localization. No runtime initializer/schema changes are planned.

# Verification Plan

Run root make verify-plan then make verify against the actual branch changes. Review linked guide paths and bilingual instruction parity. Walk through new intake, prefilled intake, missing assets, Korean localization and interrupted/resumed execution. Validate staged commit and planned/actual PR metadata with repository governance hooks.

# Impact

Changes agent behavior only for explicit project-initialization requests. Fork/clone/build/startup and existing make init/project-init retain their behavior. Future initialized forks record their own public brief, implementation and evidence; this change does not initialize the blueprint itself.

# Loop Alignment

Backend request/domain-event/background-task and frontend API/realtime/connectivity/UI loops are not applicable to this instruction/documentation change. The execution guide requires future runtime/UI changes to follow their domain guides, state/performance and page-family policies and child-first integration.

# Verification

- `make verify-plan`: backend=False, frontend=docs, areas=governance; selected root `verification-harness-test` plus lightweight text/JSON validation.
- `make verify`: passed lightweight validation and governance/harness fixtures (54 verification tests and 8 Git-hook tests). Runtime, browser, production builds and native packaging were omitted by the classifier because this task changes instructions/docs only.
- Reviewed English/Korean stage order and execution requirements against new intake, prefilled answers, missing assets, Korean primary docs, interrupted/resumed execution and explain/edit-only requests. These are instruction walkthroughs, not an autonomous-agent end-to-end run or a real project initialization.
- All six local links in the new guides resolve; both guides include the four resume states. Existing setup descriptions were corrected to include submodule/hook preparation in make init.
- `git diff --check` passed. Staged governance and actual PR metadata validation are required before delivery.
