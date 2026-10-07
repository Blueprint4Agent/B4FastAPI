# Local Git verification

Run `make hooks-install` after cloning, or use `make init`. Installation sets this clone's
`core.hooksPath=.githooks`; hooks are versioned but Git does not enable them on clone.
The B4FastAPI installer also installs hooks in the initialized B4React submodule.
A different existing hooksPath is never silently replaced.

- `commit-msg`: Conventional Commit title/body plus matching staged worklog. Integration
  merges are exempt. Stage worklog edits with implementation; unstaged logs do not count.
- `pre-push`: require a clean tree (including submodules/untracked files), verify that every
  pushed ref points to checked-out HEAD, fetch the push remote's main and use its merge base
  for the complete branch comparison. Validate each non-merge commit, then run the existing
  `make verify-plan` / `make verify` classifier. Missing history/network/dependencies or failed
  checks block the push. Commit/stash changes or switch to the desired ref and retry.
- PR title/body edits: use `PR_NUMBER=123 make git-governance-pr-check` after creating/editing
  a PR and immediately before merging. It checks actual remote metadata against local HEAD.
  Planned metadata can still be checked with PR_TITLE and PR_BODY_FILE.

Docs/copy remain cheap; behavior, UI and protected changes retain their existing scope.
Tests are not downgraded or replaced by hook-only smoke checks. `make hooks-test` tests actual
Git hook failure paths and successful pushes in isolated repositories. It joins full verification.

`make verify` stores successful command receipts under the repository Git directory in
`verification-receipts/`, plus logs in `verification-logs/`. A receipt lasts at most 24 hours
and includes command, source bytes/modes, docs, local environment/public branding files,
tool/environment context and build-output digests when relevant. Worklog Markdown is omitted
from the expensive-command fingerprint because its text and committed metadata are always
checked independently. New/deleted/modified code or config, changed tools, expired/corrupt
receipts, missing build output or a failed rerun prevent reuse. Parent delegated commands can
reuse identical child command receipts. Parent branding, contract and packaging targets still
run as needed. Receipts are local optimization evidence, not signed CI attestations.
`VERIFY_FULL=1 make verify` forces a fresh full run; manual GitHub runs never use local receipts.

GitHub workflows run only through Actions → Run workflow (or `gh workflow run`). Governance
requires a PR number; Build can validate a ref/PR and publishes an image only when requested;
Desktop Build is manually dispatched for the selected ref. No automatic PR/push/schedule/tag/
release execution remains. Main still requires PRs and resolved conversations and forbids
branch deletion/force pushes; required CI statuses are removed, with zero required approvals.

Hooks can be bypassed or not installed; GitHub therefore no longer guarantees that a merged
commit passed checks. Agents and contributors must install hooks, retain worklog evidence,
run actual PR metadata checks and merge through PRs. Do not skip hooks in normal work.

Receipt v2 canonicalizes duplicate PATH entries and Git's injected helper directory, while
retaining PATH precedence, actual tool versions/resolution and environment/config changes.
Use the same shell/toolchain for child and parent commands; a different Python installation
is a valid cache miss. Static checks and tests have separate receipts. Scoped test commands
include their complete selected suites/cases. Parent branding precedes child checks and build
and route receipts use the same child command identity. See verification.md for scope rules.
