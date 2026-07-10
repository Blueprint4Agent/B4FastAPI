# Agent Guide

Read this file first, then move to the domain guide for your task.

## Required Read Order

1. `AGENTS.md`
2. Backend task: `src/backend/BACKEND.md`
3. Frontend task: `src/frontend/FRONTEND.md`

## Documentation Sync

If implementation changes behavior, structure, or rules, update related docs in the same work cycle.

Localized documentation is maintained under `notes/<locale>/...`.
Keep localized paths synchronized with `README.md`.

## Loop Check Policy

When a developer explicitly requests loop engineering or asks whether a backend/frontend loop is needed, check the relevant domain guide before implementing.

Before committing, treat loop alignment as a default verification step:

1. Backend changes: confirm the request lifecycle, domain event, and background task loops are either followed or not applicable.
2. Frontend changes: confirm the API state, realtime refresh, desktop connectivity recovery, and UI composition loops are either followed or not applicable.
3. If a loop is intentionally skipped, record the reason in the final response and worklog when the change is committed.

## Pre-Commit Verification

Before finalizing a commit, run validation through the root `Makefile` hooks.

1. Use `make help` to confirm available workflow targets when needed.
2. Run the narrowest relevant Make target for the changed scope:
   - Backend-only: `make backend-check` and `make backend-test`
   - Frontend-only: `make frontend-format-check` and `make frontend-test`
   - Cross-stack or shared workflow changes: `make check` and `make test`
3. If a required Make target cannot run in the local environment, record the reason in the final response and worklog.
4. Do not replace Make targets with ad-hoc commands unless the Make target itself is broken or missing.

## Worklog Policy (Required)

1. Every commit must include a matching worklog entry file under `worklog/`.
2. Worklog filename format: `<number>-<short-kebab-title>.md`.
3. Worklog must record at least:
   - commit title
   - changed file scope
   - reason
   - impact
4. Do not finalize a commit without updating/adding its worklog entry.

## Git Governance

Use the repository harness when preparing branches, commits, or pull requests:

```sh
make git-governance-check
```

The harness validates the current branch, commit title, and matching worklog. Use `scripts/validate-git-governance.sh --commit-title "..." --pr-title "..." --pr-body-file <file>` to validate planned metadata before committing or opening a PR.

### Branch Naming

Branch names must use an industry-standard change type and kebab-case description:

```text
<type>/<short-kebab-title>
```

Allowed types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `ci`, `build`, `perf`, `style`, `revert`, `hotfix`.

Examples:

- `feat/api-key-pagination`
- `fix/oauth-callback-state`
- `docs/frontend-rules`
- `chore/commit-pr-governance`

### Commit Titles

Commit titles must follow Conventional Commits:

```text
<type>(optional-scope): <imperative summary>
```

Examples:

- `feat(frontend): add API key pagination`
- `fix(auth): preserve oauth callback state`
- `docs: define PR governance rules`

Commit bodies are required for non-trivial commits and must include:

```text
Changes:
- What changed.

Affected Files:
- Key files or directories changed.

Verification:
- How the change was tested or reproduced.
```

Use `COMMIT_BODY_FILE=<file> make git-governance-check` or `scripts/validate-git-governance.sh --commit-body-file <file>` to validate planned commit body sections before committing.

### Pull Request Titles and Descriptions

Create PRs as ready for review by default. Use draft PRs only when the user explicitly requests a draft or when a blocker must be resolved before review.

PR titles must use a visible type tag:

```text
[type] Concise PR title
```

Examples:

- `[feat] Add API key pagination`
- `[fix] Preserve OAuth callback state`
- `[docs] Define commit and PR governance`

PR descriptions must include:

- Summary
- Scope
- Reason
- Verification
- Documentation
- Risk / Impact

When labels are available, apply labels that match the type and affected area, such as `feat`, `fix`, `docs`, `frontend`, `backend`, `infra`, or `tests`.

### Merge Method

Use a merge commit for pull requests by default, including automatic merges:

```sh
gh pr merge <number> --auto --merge
```

Do not use squash merge or rebase merge unless the user explicitly requests that method. Validate the planned method through `make git-governance-check`; the default `MERGE_METHOD=merge` rejects other methods unless the explicit-request override `ALLOW_NON_MERGE_METHOD=true` is supplied.

Before enabling auto-merge, confirm the requested method in the resulting `autoMergeRequest`. A merge method cannot be changed after the pull request has merged; if the wrong method is registered, disable auto-merge before required checks complete and register it again with `--merge`.
