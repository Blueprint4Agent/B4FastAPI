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

## Worklog Policy (Required)

1. Every commit must include a matching worklog entry file under `worklog/`.
2. Worklog filename format: `<number>-<short-kebab-title>.md`.
3. Worklog must record at least:
   - commit title
   - changed file scope
   - reason
   - impact
4. Do not finalize a commit without updating/adding its worklog entry.
