# 0001 Worklog

- Commit title: `chore: define agent commit and worklog conventions`
- Scope: `cross-cutting`

## Changed Files

- `AGENT.md`
- `WORKLOG.md` (removed)
- `worklog/0001-agent-commit-and-worklog-convention.md`

## Reason

- Standardize commit messages for agent readability.
- Enforce per-commit worklog files under `worklog/`.
- Remove legacy root-level worklog file.

## Impact

- Future commits can be split by frontend/backend feature units with consistent format.
- Agents can trace commit intent and scope quickly from `worklog/`.
