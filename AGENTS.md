# Agent Guide

[한국어](notes/ko/AGENTS.md)

## Read order and task routing

Read this guide first, then `src/backend/BACKEND.md` for backend work or the
initialized B4React `AGENTS.md` and `FRONTEND.md` for frontend work. Read the domain
TEST guide when changing tests. Preserve unrelated working tree/submodule edits.

Operational procedures live in repository skills; read the matching file even if
this client does not discover skills automatically:

| Task | Procedure |
| --- | --- |
| Prepare or create a commit | [b4-commit](.agents/skills/b4-commit/SKILL.md) |
| Publish/update a PR or perform a requested merge | [b4-pr](.agents/skills/b4-pr/SKILL.md) |
| Create/update a GitHub issue | [b4-issue](.agents/skills/b4-issue/SKILL.md) |

Use only the requested scope; a commit-only request does not authorize an issue or
merge. For implementation tasks, finish with a commit, push and ready PR unless the
user limits publication. Review-only requests do not require publishing changes.

## Required workflow invariants

- Before implementation, create a named `<type>/<kebab-description>` task branch and
  copy [.github/WORKLOG_TEMPLATE.md](.github/WORKLOG_TEMPLATE.md) to the next
  `worklog/NNNN-description.md`. Fill the plan, design and loop impact first.
- Every authored commit must add/update a complete worklog whose Commit Title
  exactly matches it. Integration merge commits are exempt. Git validates recorded
  evidence, not when the plan was written or whether the design is correct.
- Run root `make verify-plan` then `make verify`; use `VERIFY_BASE=<base-sha>` for
  the whole branch. The [verification policy](notes/verification.md) owns scope,
  escalation and receipt rules. Do not downgrade uncertain changes or repeat valid
  unchanged checks. Record actual results and task-specific omissions in the worklog
  and final response; previous skip requests are not permanent exemptions.
- Install versioned hooks with `make hooks-install` once per clone (also in `make init`).
  Do not bypass hooks. Existing custom hooksPath requires explicit reconciliation.
  See [local hooks](notes/local-hooks.md) for hook behavior and manual Actions.
- Use Conventional Commit titles and nonempty Changes, Affected Files and Verification
  body sections for every authored commit. Validate staged metadata through Make.
- Use the existing GitHub templates. PRs are ready by default; draft requires an
  explicit request or a blocker. Keep related follow-up work in the same task PR.
- Default to merge commits. Squash/rebase requires an explicit user request. Check
  actual PR metadata after creation/edits and immediately before a requested merge.
  Do not disable PR/history protection or bypass repository admin permissions.
- Synchronize changed behavior/structure/rules with related docs, including
  `notes/ko/`; keep localized entry links in README synchronized.

## Project Initialization Trigger

When the developer requests initialization of this project (for example,
`프로젝트 초기화하기`, `새 프로젝트 시작`, or `initialize this project`), read
[the project onboarding flow](PROJECT_ONBOARDING.md) and start its staged intake.
This repository instruction is the trigger; no installed skill, slash command,
GitHub event or application startup hook is required. Reuse answers already given,
ask only the next missing stage, and apply the collected setup when intake is complete.
Requests to explain initialization or edit this workflow do not initialize the project.
For a resumed session, read `PROJECT_BRIEF.md` if present before asking questions.
Distinguish actual setup from a rehearsal; use an independent disposable clone for
trigger checks. Before applying or declaring completion, follow the mandatory
[surface and rollback audit](PROJECT_ONBOARDING_AUDIT.md), including UI/console/document
brand remnants, language behavior and evidence for every applicable surface.

## B4React integration

`src/frontend` pins a separate repository. Initialize missing submodules with
`git submodule update --init --recursive` after preserving local edits. Frontend
changes need a named child branch and PR; merge there before updating the parent
pin. Parent worklogs own integration, contracts and packaging; child worklogs own
frontend changes. Never follow `--remote` in CI or automatically overwrite child
contracts from the provider. Follow [integration and contract order](notes/frontend-submodule.md).

## Domain review obligations

Review applicable loops before implementation and completion: backend request,
domain event and background task; frontend API state, realtime refresh, desktop
recovery and UI composition. Record non-applicable/skipped loops and reasons.
Explicit loop-engineering requests require reading the domain guide first.

Backend services orchestrate; repositories own relational sessions, queries,
transactions, ORM writes and driver errors. Manually review the persistence and
router/service interface sections of `src/backend/BACKEND.md`, including main.py
handlers, domain errors and cross-service private access. Passing import checks
alone does not establish compliance; distinguish violations, consistency and allowed
technical/transport adapters. Redis is outside the relational boundary.

For frontend runtime changes, follow the child [state/performance policy](src/frontend/notes/react-performance.md)
and record ownership, justified memoization and observed evidence. Avoid blanket
memo wrappers or new state libraries without need; independent optimizations stay
in separate task PRs. For UI changes, follow the child [page-family policy](src/frontend/notes/page-families.md):
choose a peer before editing, reuse its composition, compare real rendering and
record scoped exceptions. Reference screenshots do not override the host family.
