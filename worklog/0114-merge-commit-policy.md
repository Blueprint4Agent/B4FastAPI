# commit title

docs: define merge commit policy

# changed file scope

- AGENTS.md
- Makefile
- scripts/validate-git-governance.sh
- .github/PULL_REQUEST_TEMPLATE.md
- .github/PULL_REQUEST_TEMPLATE/ko.md
- worklog/0114-merge-commit-policy.md

# reason

- The repository defined branch, commit, and PR metadata rules but did not define a merge strategy.
- An automatic merge can complete with the wrong method before its configuration is corrected.

# impact

- Pull requests use merge commits by default, including automatic merges.
- Squash and rebase require an explicit user request and governance override.
- Contributors are instructed to verify the registered auto-merge method before required checks complete.
