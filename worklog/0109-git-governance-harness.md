# commit title
chore(git): add commit and PR governance harness

# changed file scope
- Makefile
- AGENTS.md
- notes/ko/AGENTS.md
- .github/PULL_REQUEST_TEMPLATE.md
- .github/PULL_REQUEST_TEMPLATE/ko.md
- scripts/validate-git-governance.sh
- worklog/0109-git-governance-harness.md

# reason
- Standardize branch names, commit titles, PR titles, PR descriptions, and matching worklog checks.
- Standardize commit body sections for work summary, affected files, and verification.
- Give contributors and agents a local harness before opening pull requests.
- Document PR title tags and branch naming conventions in both English and Korean guides.

# impact
- `make git-governance-check` now validates Git metadata conventions.
- Planned commit body files can be checked for `Changes:`, `Affected Files:`, and `Verification:` sections.
- PR templates now remind authors to use typed titles, typed branches, Conventional Commits, and matching labels.
- Future PR creation can follow consistent type tags such as `feat`, `fix`, `docs`, and `chore`.
