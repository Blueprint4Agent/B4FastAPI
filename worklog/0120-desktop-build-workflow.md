# Commit Title

ci: add desktop build workflow

# Changed File Scope

- GitHub Actions desktop build workflow.
- Deployment guide and Korean localized deployment guide.
- Frontend README and Korean localized frontend README.

# Reason

Desktop app builds need a repeatable GitHub Actions workflow so macOS, Linux, and Windows Tauri
bundles can be generated consistently outside a local developer machine.

# Impact

- Adds a manual, tag, and release-triggered desktop build workflow.
- Builds unsigned Tauri desktop bundles on macOS Apple Silicon, macOS Intel, Linux x64, and Windows x64.
- Uploads generated installer/bundle files as GitHub Actions artifacts for internal verification.
- Documents desktop build API origin injection through `api_base_url`, `DESKTOP_API_BASE_URL`, or local fallback.

# Verification

- `make check`
- `make test`
- `git diff --check`
- Ruby YAML parser for `.github/workflows/desktop-build.yml`
- `make frontend-desktop-build`
