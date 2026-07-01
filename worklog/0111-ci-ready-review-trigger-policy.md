# commit title
ci: avoid duplicate PR checks on ready for review

# changed file scope
- .github/workflows/build.yml
- AGENTS.md
- notes/ko/AGENTS.md
- worklog/0111-ci-ready-review-trigger-policy.md

# reason
- PR checks currently run on draft PR creation through the `opened` event and run again when the PR is marked ready through `ready_for_review`.
- The preferred workflow is to create ready PRs by default and avoid duplicate validation when draft state changes.

# impact
- Pull request CI now runs for `opened`, `synchronize`, and `reopened`, but not for `ready_for_review`.
- Agent instructions now state that PRs should be created ready for review by default unless a draft is explicitly requested or blocked.
