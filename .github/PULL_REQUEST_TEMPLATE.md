## Summary

Describe the change in one or two sentences.

## Title / Branch Rules

- PR title uses `[type] Concise title`, for example `[feat] Add API key pagination`.
- Branch uses `<type>/<short-kebab-title>`, for example `feat/api-key-pagination`.
- Commit title uses Conventional Commits, for example `feat(frontend): add API key pagination`.
- Commit body includes `Changes:`, `Affected Files:`, and `Verification:`.
- Apply labels that match the type and affected area when available.
- Merge with a merge commit by default. For auto-merge, use `gh pr merge <number> --auto --merge`.
- Do not use squash or rebase unless the user explicitly requests that method.

## Scope

- Backend:
- Frontend:
- Docs:
- Tests:
- Infrastructure:

## Reason

Why is this change needed?

## Verification

- [ ] Backend tests passed
- [ ] Frontend tests passed
- [ ] Build passed
- [ ] Manual verification completed

## Documentation

- [ ] Documentation updated
- [ ] Korean documentation updated, if user-facing behavior changed
- [ ] Not applicable

## Risk / Impact

Describe behavior changes, migration needs, compatibility concerns, or rollout notes.

## Related Issues

Closes #
