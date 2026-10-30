---
name: b4-pr
description: Publish or update B4FastAPI pull requests and validate metadata; merge only when the task authorizes merging.
---

# B4 pull request

Resolve the target Git root and remote repository. Read its AGENTS.md and existing
PR template (`.github/PULL_REQUEST_TEMPLATE.md`, or the Korean alternative).
Use the child repository's own workflow for B4React changes; parent gitlink updates
follow `notes/frontend-submodule.md` after the child PR merges.

1. Inspect local branch/status, target branch, authored commits and any existing PR
   for this head. Update the existing task PR rather than creating a duplicate.
   If commits remain to be prepared, read the adjacent `b4-commit/SKILL.md`.
2. Summarize the final behavior and evidence using the current template. Remove
   placeholder checkboxes/text and include observed checks and justified omissions.
   Link only real related issues; use `Closes` only when the PR actually resolves one.
   Inspect available repository labels and select matching type/area labels.
3. Use `[type] Concise title`; exact constraints come from
   `scripts/validate_git_governance.py` (currently an ASCII letter/digit after the tag).
   Write the body to a temporary UTF-8 file; validate PR_TITLE and PR_BODY_FILE
   together through `make git-governance-check`. The checked-out HEAD must be the
   intended authored commit; uncommitted work must be resolved before pushing.
4. Push the checked-out branch with normal hooks. Create a ready PR by default;
   draft requires a user request or a blocker. For CLI bodies use `--body-file`.
   If a create/update request has an uncertain result, query remote state before retrying.
5. Inspect actual title, body, labels, base/head, head SHA, draft state and issue links.
   Run `PR_NUMBER=<number> make git-governance-pr-check` after creation or edits.
   The checker does not establish labels, draft state or issue-link correctness;
   inspect those explicitly. Report the PR URL and whether it is open or merged.

## Requested merge

Only enter this section when merging is authorized. Recheck actual PR metadata,
review/conversation blockers and `PR_NUMBER=<number> make git-governance-pr-check`
immediately before merge. Do not alter branch protection to obtain a merge.

Use merge commits, including `gh pr merge <number> --auto --merge` when auto-merge
is appropriate. Squash/rebase requires an explicit user request and planned
`MERGE_METHOD=<method> ALLOW_NON_MERGE_METHOD=true make git-governance-check`.
After registration, inspect `autoMergeRequest.mergeMethod`; it must be MERGE for
normal merges. If it differs and the PR is still open, disable auto-merge and
correct it. If GitHub merges immediately, inspect the merged result instead of
claiming auto-merge is pending. Use one watcher only when checks are actually pending.
See `notes/local-hooks.md` for this repository's manual-only Actions policy.
