# Agent-led project initialization

[한국어](notes/ko/PROJECT_ONBOARDING.md)

This is the repository's conversational setup procedure, entered through
[AGENTS.md](AGENTS.md). A developer says **“프로젝트 초기화하기”** or
**“initialize this project”** to an agent working in their copied/forked repository.
An agent must read and follow AGENTS.md for this routing to work; this is not an
executable listener or an automatic fork/clone event. Do not initialize the blueprint
when asked only to explain, review or change this procedure.

## Intake

Use the developer's conversation language. First read existing public project files
and any `PROJECT_BRIEF.md`, inspect parent/child status, and preserve unrelated edits.
Follow the repository's task-branch and planned-worklog rules before writing files.
Ask one stage per turn, skipping questions already answered. A stage can group
closely related choices; do not present the whole questionnaire at once. Wait for
answers rather than inventing project intent or treating silence as approval.

| Stage | Collect | Example next question |
| --- | --- | --- |
| 1. Name | Display name; propose a short name, kebab-case slug and reverse-DNS ID for acceptance or correction | What is the project name? I can propose the technical names from it. |
| 2. Overview | Purpose, target users, main problem, first working user journey and initial scope | Who uses it, and what should they accomplish on the first screen? |
| 3. Screens | Images, URLs, local files or a written screen description; priority screens and what to adopt | Do you have a reference screen, or should we define the first screen in words? |
| 4. Brand | Existing icon/logo source; light/dark treatment; create a simple asset, use a temporary one, or defer; web/native targets | Do you have a brand icon, or should we create a simple one from a direction you choose? |
| 5. Languages | UI default and supported locales; development-document primary language and translation scope; agent conversation language if different | What should the UI and development-document languages be? For example: Korean UI with English available, Korean primary docs. |
| 6. Features | Login, email and OAuth; web/desktop targets and requirements needed for the first journey | Does the first version need login, email or OAuth, and will it run on web or desktop? |

Proposals are suggestions until accepted. A user may explicitly choose “no reference,”
“temporary icon,” “web only,” or another deferral. Record it with its effect instead
of repeatedly blocking intake. If a supplied image/link cannot be accessed, explain
which input is missing and ask for an accessible file or written direction. Never
claim to have inspected a reference that was not read. Do not collect secrets in the
conversation or public files; provider credentials belong in ignored env/secret stores.

Record accepted public answers incrementally in root `PROJECT_BRIEF.md`, in the
chosen document language once known. Tell the developer this file is committed
project documentation; redact private source material or use an approved public
summary. Keep screenshots/source assets in agreed local project paths; record
external references with their purpose. Do not copy third-party logos or screen
assets into the product without permission to use them.

The brief is the resumable source of truth for intent and progress. Include:

- Status: `collecting`, `applying`, `blocked`, or `complete`; current/next stage.
- Accepted name, short name, slug, identifier, overview, audience and first journey.
- Screen references and intended UI scope; branding source, target surfaces and deferrals.
- UI default/supported languages, primary document language and document inventory/scope.
- Feature/target choices, unresolved required inputs and explicit deferrals.
- Execution checklist with affected paths, completed steps, verification evidence and blockers.

Use `project.json` as the executable identity/features source and the brief for
intent and workflow state. Do not add overview, references or language fields to
`project.json`: its current schema rejects those fields. Resolve disagreements with
the developer instead of silently overwriting an existing project's configuration.

## Start initialization

When required answers are collected and optional omissions are explicitly resolved,
show a concise accepted setup and announce **“프로젝트 초기화를 시작합니다.”**
(or its conversation-language equivalent). Start implementation without another
blanket permission question. Ask again only for a genuinely unresolved input or an
action requiring separate authorization. An initialization request does not authorize
production migration, deployment, purchasing assets or external submission.

1. **Prepare.** Follow root and applicable domain guides. Initialize the pinned child
   before reading its guides with `make frontend-init`. Set the brief to `applying`,
   update the task worklog design/verification/loop plan, and use the required named
   branch. For child source changes use a B4React task branch and PR, merge there
   before updating the parent gitlink. Do not commit source edits on a detached child.
2. **Apply identity.** Run `make init` and `make install` as needed, create/update
   public root `project.json` from the accepted values, and place approved source
   logos under `branding/`. Run `make project-plan`, `make project-init`, then
   `make project-check`. Preserve unrelated env values and configured secrets.
   Follow [PROJECT_SETUP.md](PROJECT_SETUP.md) for schema, asset limits and ownership.
3. **Implement screens.** Build the agreed first journey using the frontend domain,
   page-family and state/performance policies. Compare an existing peer page before
   adapting layout and components to the references. A reference establishes intent;
   it does not replace the host UI rules. Do not stop at recording reference URLs or
   changing the title. Implement backend contracts only when the agreed journey needs
   them, following the backend guide. Do not fabricate working integrations or data.
4. **Finish branding.** Check visible navigation, page/browser title, favicon and
   agreed product surfaces. The existing initializer generates the web brand and
   desktop product identity; favicon and Tauri installer/native icons are separate
   source/generated assets and must be handled explicitly for selected targets.
   Use available asset tooling when generation is requested; if unavailable, ask for
   a source or agreed temporary alternative. Do not mark an unbuilt native package
   or an uncreated asset as verified. Keep original brand sources in the parent;
   ignored child `project.local.json` and `public/project-brand/` are regenerated inputs.
5. **Apply UI language.** Inspect the actual locale initialization, persistence,
   fallback and document language metadata before changing defaults. Ensure a fresh
   browser gets the chosen default, existing explicit user preferences remain valid,
   and retained locales still work. Adding a language field to the brief does not
   change runtime behavior. Change the child's source through its governed workflow
   if the current identity generator cannot express the selection.
6. **Localize development documents.** Inventory active entrypoints and linked domain,
   setup, verification and deployment docs. For Korean primary docs, use the maintained
   `notes/ko/` counterparts where available and translate missing material; put Korean
   content in the active root/domain entrypoints, including AGENTS.md and README.md.
   Update linked first-party guides in the agreed inventory so developers do not
   immediately return to English-only instructions. Preserve commands, paths, code
   identifiers, API names, obligations and historical worklogs. Keep English copies
   and language navigation at explicit paths when requested; adjust links relative
   to each destination and update README's locale map. Do not mass-replace English
   tokens in code or merely link to a Korean document and claim translation is done.
   Record deliberately excluded third-party/generated/history files and remaining
   agreed translations in the brief. Validate links and instruction parity.
7. **Verify and deliver.** Review each accepted item against actual changes. Run root
   `make verify-plan` then `make verify` with branch scope, and follow child/parent
   integration checks. Run browser checks for screen changes, inspect brand surfaces
   and test language defaults in a fresh context and with a saved language choice.
   Verify document links, language navigation and retained governance rules. Record
   selected/omitted checks and evidence in the worklog and brief; follow commit/PR
   governance. Report completed items, deferrals and unresolved blockers. Set status
   to `complete` only when the agreed implemented scope and required verification
   are finished. A blocked check or inaccessible required asset stays visible.

## Resume or change direction

Read the brief, current manifest, Git diff, child status and recorded check evidence.
Continue from the next incomplete stage; do not repeat accepted questions or blindly
reapply everything. If the developer changes a choice, update the brief and reconcile
only affected outputs, invalidating checks as needed. Never reset unrelated changes,
rotate configured secrets, reset history or delete prior work to restart intake.
For an existing running deployment, resolve resource/migration impact before changing
identity or Compose namespaces; the new-project initializer is not a migration tool.

## Acceptance examples

- **Bare request:** “프로젝트 초기화하기” starts by asking the project name, then
  proceeds through the missing stages. It does not immediately apply template defaults.
- **Prefilled request:** “Acme, a Korean team dashboard; docs in Korean; web only”
  reuses those answers and asks about the missing first journey/references/brand/features.
- **No assets:** An explicit temporary-icon/no-reference choice permits the agreed
  first screen to proceed; the brief records the temporary asset and its surfaces.
- **Korean docs:** Verify active root/domain instructions and their linked inventory,
  not just a `language: ko` note. Commands and governance requirements remain intact.
- **Interrupted run:** Read `PROJECT_BRIEF.md`, inspect what was actually applied,
  then resume without overwriting completed or unrelated work.
- **Explain/change flow:** “How is init triggered?” or “add an initialization flow”
  explains/edits this procedure without collecting a real project name or applying it.
