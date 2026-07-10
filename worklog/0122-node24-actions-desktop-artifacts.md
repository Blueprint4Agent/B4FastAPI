# Commit Title

ci: update actions for Node 24 desktop artifacts

# Changed File Scope

- GitHub Actions build workflow.
- GitHub Actions desktop build workflow.
- Worklog entry for CI workflow maintenance.

# Reason

GitHub Actions is deprecating Node 20 action runtimes. The desktop build upload step also relied
on static bundle globs that miss target-specific Tauri output directories such as macOS
cross-target builds.

# Impact

- Moves official checkout, setup-node, and upload-artifact actions to Node 24-compatible major
  versions.
- Runs frontend CI dependency installation and builds with Node 24.
- Uploads desktop bundles from `tauri-action`'s generated `artifactPaths` output instead of
  assuming a single `target/release/bundle` directory.

# Verification

- `ruby -e 'require "yaml"; Dir[".github/workflows/*.yml"].each { |f| YAML.load_file(f); puts "ok #{f}" }'`
- `git diff --check`
- `make check`
- `make test`
