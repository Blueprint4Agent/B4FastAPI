# 0002 Worklog

- Commit title: `chore: add repository baseline and ignore policy`
- Scope: `cross-cutting`

## Changed Files

- `.editorconfig`
- `.gitignore`
- `README.md`
- `worklog/0002-repo-baseline-and-ignore-policy.md`

## Reason

- Track repository-wide editor conventions.
- Prevent local runtime artifacts (`.db`, frontend/backend build output, editor files) from being staged.
- Align documentation entry link to `AGENT.md`.

## Impact

- Future commits stay cleaner with fewer accidental local files.
- Agent/docs entry path is consistent with the current repository structure.
