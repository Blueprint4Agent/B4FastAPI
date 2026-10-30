---
name: b4-commit
description: Prepare and create B4FastAPI commits using worklogs, scoped Make verification and staged governance checks.
---

# B4 commit

Resolve the target Git root first; paths and commands below are relative to that root.
This procedure belongs to B4FastAPI. For changes inside the B4React submodule, follow
that repository's guides and templates instead of applying parent-only assumptions.
Read root AGENTS.md; inspect status, branch, diff and existing worklogs. Preserve unrelated edits.

1. Confirm the named task branch and pre-implementation worklog plan already exist.
   If missing, record the gap honestly; never claim a retrospective plan preceded work.
   Use `.github/WORKLOG_TEMPLATE.md` as the section source of truth, not a copied schema.
2. Review implementation, documentation and applicable domain loops. Run root
   `make verify-plan` then `make verify`. For all branch changes set VERIFY_BASE to
   the intended target merge-base. Follow `notes/verification.md` for scope and reuse;
   inspect failure summaries and fix causes without bypassing checks.
3. Record observed results, selected scope, omissions/reasons and impact in the worklog.
   Use a Conventional Commit title and matching worklog Commit Title. Allowed types
   and exact title constraints are defined by `scripts/validate_git_governance.py`.
   Its current title format requires an ASCII lowercase letter/digit after `: `.
4. Write a temporary UTF-8 commit-message file with the title and nonempty
   `Changes:`, `Affected Files:`, `Verification:` sections. Every authored commit
   requires these sections, including docs-only commits. Stage only intended files
   and the matching worklog; inspect `git diff --cached`.
5. Run `COMMIT_TITLE='<title>' COMMIT_BODY_FILE=<file> make git-governance-check`
   against the staged snapshot. Restage and revalidate if relevant files change.
   Commit with `git commit -F <file>`; keep commit-msg hooks enabled.
6. Report the commit and actual verification. Continue to PR publication only when
   within the requested workflow. A commit-only task ends here.

Use the existing checker rather than reproducing its validation in a new script.
For hook failures or receipt troubleshooting, read `notes/local-hooks.md`.
