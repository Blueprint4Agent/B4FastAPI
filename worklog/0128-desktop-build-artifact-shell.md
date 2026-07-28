# Commit Title

fix(ci): run desktop artifact path parser in bash

# Changed File Scope

- `.github/workflows/desktop-build.yml`

# Reason

The follow-up Desktop Build verification showed Windows successfully built the desktop bundles, but the artifact path parser failed because the workflow step used a bash heredoc while GitHub Actions defaulted the Windows step shell to PowerShell.

# Impact

The artifact path parser now runs under bash on every matrix platform, matching the heredoc syntax already used by the step. Backend and frontend runtime loops are not applicable because this change only updates CI workflow execution.
