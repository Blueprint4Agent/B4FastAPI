# Commit Title

ci: schedule desktop main builds and release uploads

# Changed File Scope

- GitHub Actions desktop build workflow.
- Deployment guide and Korean localized deployment guide.

# Reason

Desktop builds should run automatically for releases and scheduled `main` verification, not only by
manual workflow dispatch. Release builds should also attach generated desktop bundles to the
matching GitHub Release assets.

# Impact

- Adds a scheduled `main` desktop build at `01:00 KST`.
- Keeps generated scheduled desktop bundles as workflow artifacts for internal verification.
- Uploads release/tag desktop bundles to matching GitHub Release assets.
- Grants the desktop workflow `contents: write` so release assets can be uploaded.

# Verification

- `make check`
- `make test`
- `git diff --check`
- Ruby YAML parser for `.github/workflows/desktop-build.yml`
