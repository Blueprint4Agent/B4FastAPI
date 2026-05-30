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
