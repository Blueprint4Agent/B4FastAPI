# Initialization coverage and completion audit

[한국어](notes/ko/PROJECT_ONBOARDING_AUDIT.md)

Use this checklist with [onboarding](PROJECT_ONBOARDING.md), before applying changes
and again before claiming completion. In the actual target project, create
`PROJECT_INITIALIZATION_AUDIT.md` with the rows below. This file is a procedure/template,
not evidence that any project has passed. The agent must fill evidence from actual tools.

## Target and rollback record

Record actual initialization versus trigger rehearsal, absolute target path, parent
and child remotes/branches/pins, initial dirty files, accepted public configuration,
and the input/output inventory. Rehearsals use an independent disposable clone with
its own Git configuration, example env files and pinned child; never copy credentials,
change upstream env, or push from that clone. A worktree shares Git configuration,
so it alone is not sufficient isolation for hook-install experiments.

For real setup, capture existence, bytes and modes of files that will be replaced,
including ignored generated config/assets, before `make init` or any generator.
Keep private backups ignored and never print secret content. Record new paths to
remove on rollback; distinguish existing generated outputs from newly created ones.
Recover authored files and private env exactly. Regenerate derived builds if their
original bytes were not captured, and state that this is regeneration, not byte identity.

## Required surface inventory

Give every row: actual paths/owners, requested result, implementation path, status,
verification command or visual artifact, and remaining findings. Allowed completion
states are **verified**, **not applicable (reason)**, or **explicitly deferred (decision
and impact)**. Missing rows, planned-only evidence and unresolved required items block
completion. Do not use a filled checkbox as proof that rendering was checked.

| Surface | Required inspection and evidence |
| --- | --- |
| Shared brand | Navbar, sidebar, public/auth shell, responsive and light/dark marks; inspect actual image requests, not only generated filenames. |
| Secondary UI | Showcase/avatar samples, dialogs, image viewer titles, notifications/toasts and empty/loading/error screens with hardcoded brands. |
| Browser identity | Actual title, favicon request/response, HTML lang, sharing/OG/Twitter metadata; web manifest/apple-touch icons if present. |
| Brand assets | Light/dark fallbacks, SVG text, raster images, preview screenshots, README screenshots and embedded logos; inspect images visually. |
| UI language | Fresh browser with a different OS locale, retained English/Korean switch and saved preference after reload; scoped storage and fallback. |
| Backend identity | APP_NAME/API title, public generated identity and configured email/service names; inspect public values without exposing private env. |
| Console | Interactive/plain/redirected startup, ASCII art/tagline, shutdown farewell and failure paths; old logos can survive a renamed log prefix. |
| Messages | Welcome inbox records and localized rendering, auth/lifecycle email brand paths; no real email/provider call for a branding test. |
| Documents | Active root/domain/setup/verification/deploy guides, linked first-party docs, image captions and service-name examples. |
| Document language | Actual body text and navigation, incomplete translated sections and relative links/anchors; preserve executable commands and governance. |
| Commit/PR language | User-selected title/body language, while preserving Conventional Commit types, PR tags and required machine section names. |
| Public introduction | Default-only /about/discovery pages must not advertise the upstream product as the configured service. |
| Desktop | Product/window names and installer/native icons only for selected targets; web-only must record a scoped reason. |
| Technical identity | Distinguish runtime display names from module/package IDs, storage keys, event names, Stripe metadata and contract namespaces. |
| Origin/history | Preserve legitimate upstream URLs, licenses, source provenance and historical worklogs; explain each retained reference category. |
| Feature/runtime scope | Login/email/OAuth, restart/build requirements, configured provider dependencies and explicit deferrals. |

## Inventory before implementation

Search the actual project, not a remembered list of two branding keys. Search current
and prior names, abbreviations, slugs, browser titles and logo filenames. For example:

```sh
rg -n -i 'b4a|blueprint4agent|blueprint4fastapi|b4fastapi|b4react' src/backend src/frontend/src src/frontend/public notes README.md AGENTS.md PROJECT_SETUP.md DEPLOY.md
rg --files branding src/frontend/public notes/assets
```

Also inspect the HTML/build generators and ignored generated branding inputs. Do not
scan private env values into public reports. Text searches do not inspect PNG/WebP
pixels; identify and open relevant images separately. Source fallback strings and
upstream URLs can remain valid: record their role and prove that an active configured
surface uses its override. Do not rename compatibility keys or rewrite source URLs
just to make a search empty. A visibly rendered old logo is not provenance merely
because its filename belongs to the template.

List mismatches between the current initializer's owned fields and the requested
surfaces before editing. Existing `readProjectConfig()` / `__PROJECT_BRAND__` and
backend settings are the preferred owners. No project config means existing defaults;
configured values override the corresponding public surfaces. Do not introduce a
second global config or read a parent's files from the independent frontend.
Unsupported choices require implementation in the actual downstream target and its
governed child repository, or an explicit unresolved item; do not quietly claim that
writing the brief applies them. A rehearsal does not authorize fixes in upstream.

## Completion gate

After implementation settles, rerun the inventory and classify every remaining
finding as a verified fallback, legitimate technical/origin reference, explicit
scope exclusion, or unresolved defect. Keep paths/line numbers and evidence. Original
screenshots may remain only as an explicit decision with their original-template
status visible; changing their alt text to the new brand is not rebranding the image.
A name in a document is not the same as an executed console or browser observation.

Before broad verification, finish the surface inventory and a focused smoke check;
do not repeatedly launch the full suite while still discovering obvious missing
surfaces. Then use root `make verify-plan` / `make verify` without manually narrowing
shared or unknown impact. Record executed versus merely planned commands, changed
implementations versus unchanged consumers, reasons for broader checks, receipt reuse,
failures and final results. Unchanged code can still need regression tests after
shared i18n/config changes. Do not call every broad check redundant or silently skip it.
Verification-cache improvements belong in their own task, not the initialization PR.

Required acceptance scenarios:

- No project config: original branding, fallback assets and browser-language behavior.
- Configured name and logos: all applicable surfaces use the override in both themes.
- Identical name/short_name and localized names: assertions target the intended surface,
  rather than assuming the visible text occurs only once.
- Korean default in an English browser: fresh entry is Korean; explicit English choice
  survives reload. Tests selecting English must not mask the fresh-default test.
- Missing dark logo and optional settings: intentional fallback, not a mixed old/new brand.
- Configured project: default-only public introduction remains excluded; assert this
  alternative behavior instead of skipping the test or expecting the template page.
- Resume: inventory applied outputs; keep accepted answers and unrelated changes.
- Rehearsal/rollback: source, env and pinned child of the original workspace remain intact.

Set the brief to complete only when the accepted scope and this gate are satisfied.
Report explicit deferrals and remaining references. This is an agent execution
obligation supported by tests; the document itself is not an automated visual guarantee.
