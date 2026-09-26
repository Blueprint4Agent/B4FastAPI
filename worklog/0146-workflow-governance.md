# Commit Title

ci(governance): enforce PR workflow and committed worklogs

# Changed File Scope

Agent guide, workflow documentation/templates, governance scripts, Makefile, PR CI,
versioned main ruleset and the B4React submodule pointer.

# Reason

Make the documented branch/worklog/PR workflow enforceable in both repositories.

# Design

Start a named branch before writing the worklog plan. Validate staged content locally
and each non-merge commit in the PR range in CI. Read PR metadata from the event JSON.
Require PRs and named checks on main after the checks are available.

# Verification Plan

Run the repository Make checks and governance check on the staged snapshot.
Observe PR governance and existing CI checks before requiring them on main.

# Impact

Untracked worklogs and empty headings no longer satisfy commit checks. Each authored
commit needs a matching worklog title. PR metadata edits trigger governance again.
Existing runtime behavior and API contracts are unchanged.

# Loop Alignment

Backend request/event/task and frontend API/realtime/connectivity/UI loops are not
applicable: this change only affects development workflow and repository policy.

# Verification

- Root make check and B4React make check/build passed.
- B4React PR #1 passed Git governance and Frontend checks, then merged as c7f0eef.
- B4React main ruleset 24035784 now requires PRs, resolved conversations, and
  Git governance/Frontend checks; auto-merge enabled. Approval count remains zero.
- Parent main ruleset 16499496 will be updated after this PR emits Git governance.
- Staged governance validation is required immediately before commit.
- Local tests not run; automated tests passed in child CI and remain enabled in parent CI.
