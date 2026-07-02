# Commit Title

ci: use main tag for manual main image publishes

# Changed File Scope

- GitHub Actions build workflow image tag resolution.
- Deployment guide and Korean localized deployment guide.

# Reason

Manual main image publishes should use the clear `main` image tag instead of `manual-main`.
The scheduled main image remains distinct as `nightly-main`.

# Impact

- Scheduled main image publishes continue using `nightly-main`.
- Manual image publishing defaults to the `main` ref and `main` image tag when no ref is provided.
- Manual publishing with `ref=main` also uses the `main` image tag.

# Verification

- `make check`
- `git diff --check`
- Ruby YAML parser for `.github/workflows/build.yml`
