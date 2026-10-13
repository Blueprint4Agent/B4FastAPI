# Commit Title

feat(frontend): integrate guided prompt builder

# Changed File Scope

src/frontend gitlink, README.md, notes/prompt-builder.md, notes/ko/prompt-builder.md, worklog

# Reason

Help users turn a feature idea or a new service into a complete harness-aware implementation prompt, available below Home in production and development.

# Design

Lazy public /prompt-builder route inside existing AppShell. Reuse MainPageTemplate settings-family shell, SelectionCard, TextareaField, Button, Modal and InlineMessage. Centered capsule welcome, two path cards, then one question at a time with short reduced-motion-aware transitions and progress. Page-local separate feature/project drafts with four questions: name, multi-select scope, capabilities/RBAC, and delivery; review/edit then deterministic localized Markdown generation, clipboard fallback and Blob download. Both paths first ask the feature name, then multi-select implementation areas and API/database/auth/realtime/jobs/uploads/billing/tests/deployment elements. Required/optional badges and Skip for optional questions keep the flow explicit. Only the name requires typing by default; optional notes and a required deployment target appear in context. Capabilities use multi-select cards; the editable Guest/User/Manager/Admin matrix selects read/create/update/delete and own/all data. Shared FormCheckbox and DropdownMenu own permission controls. No API, persistent storage, external AI or new dependency. User refinements: remove introductory prose, use existing pill/pill-secondary navigation buttons, a distinct FilePenLine icon, and a scoped low-contrast animated ambient background (static for reduced motion).

# Verification Plan

Unit tests for draft isolation, four-step validation, RBAC and completion boundaries; production-config browser journeys for both paths, edits, validation, copy failure and download. Compare General family header/surface at 390/1440 light/dark with screenshots; test navigation across shell modes. Run make verify-plan / make verify, production routes and Git governance.

# Impact

Adds a guest-accessible production menu and lazily loaded client-only wizard. Existing authentication and deployment settings remain authoritative. Drafts last only while the page is mounted. No schema/migration or deployment action.

# Loop Alignment

UI composition loop applies through existing shell and controls. API state, realtime, desktop recovery, backend request/event/task loops not applicable: no new HTTP or server state. Existing app config/connectivity gate remains unchanged.

# Verification

B4React PR #91 merged with a merge commit at 750532ff15d07e836ea9b9e095eff972977a2ae4; child commit cf90808. Child make verify-plan selected full frontend; make verify and pre-push hook passed check, 209 unit/component/integration tests, 250 browser cases (10 prompt scenarios), 15 production route cases, 11 public discovery cases and style-studio checks. Actual child PR metadata validated before merge. Bilingual flow evaluation covers four questions, one required text field, optional RBAC defaults, eight screens overall and remaining domain-rule clarification. Root make verify-plan selected backend=False/frontend=full. Root make verify passed hooks-test, project-brand, delegated child check/test/UI/routes/style checks, frontend-contract-check frontend-package-verified, and project-build-test. Integration contract/package checks passed against the merged pin; no backend suite was selected because no backend implementation changed. Backend request/event/task and frontend API/realtime/desktop loops are not applicable because this page introduces no server state. Production route availability is verified; no live deployment performed.
